"""
DiscoveryAgent — 공개 채용 소스에서 공고 탐색
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from itertools import product
from typing import Iterable, List, Optional, Tuple
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from core.models import FilterConfig, PostingCandidate


class DiscoveryAgent:
    """원티드 API와 사람인 검색 결과에서 공고를 수집한다."""

    WANTED_URL = "https://www.wanted.co.kr/api/v4/jobs"
    WANTED_COUNTRY = "kr"
    WANTED_REFERER = "https://www.wanted.co.kr"
    SARAMIN_URL = "https://www.saramin.co.kr/zf_user/search/recruit"
    SAMSUNG_URL = "https://www.samsungcareers.com/hr/"
    USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    )
    SAMSUNG_PERIOD_RE = re.compile(r"(20\d{2}\.\d{2}\.\d{2})\s*~\s*(20\d{2}\.\d{2}\.\d{2})")

    def __init__(self):
        self.logger = logging.getLogger("DiscoveryAgent")
        self._samsung_cache: Optional[List[PostingCandidate]] = None  # 1회 수집 캐시

    def fetch_samsung_once(self) -> List[PostingCandidate]:
        """Samsung Playwright 수집을 1회만 실행하고 캐싱."""
        if self._samsung_cache is None:
            try:
                self._samsung_cache = self._fetch_samsung(None)
            except Exception as exc:
                self.logger.warning("Samsung 수집 실패: %s", exc)
                self._samsung_cache = []
        return self._samsung_cache

    def run(self, config: FilterConfig, samsung_candidates: Optional[List[PostingCandidate]] = None) -> List[PostingCandidate]:
        candidates: List[PostingCandidate] = []

        try:
            candidates.extend(self._fetch_wanted(config))
        except Exception as exc:
            self.logger.warning("Wanted 수집 실패: %s", exc)

        try:
            candidates.extend(self._fetch_saramin(config))
        except Exception as exc:
            self.logger.warning("Saramin 수집 실패: %s", exc)

        # Samsung은 외부에서 주입받거나 직접 수집
        if samsung_candidates is not None:
            candidates.extend(samsung_candidates)
        else:
            try:
                candidates.extend(self._fetch_samsung(config))
            except Exception as exc:
                self.logger.warning("Samsung 수집 실패: %s", exc)

        deduped = list(self._deduplicate(candidates))
        for candidate in deduped:
            self._apply_filter(candidate, config)

        return sorted(deduped, key=lambda item: (not item.passed, item.company, item.role))

    def _fetch_wanted(self, config: FilterConfig) -> List[PostingCandidate]:
        headers = {
            "User-Agent": self.USER_AGENT,
            "Referer": self.WANTED_REFERER,
            "Accept": "application/json",
        }
        roles = config.roles or [""]
        candidates: List[PostingCandidate] = []

        with httpx.Client(headers=headers, timeout=20.0, follow_redirects=True) as client:
            for role in roles:
                try:
                    params = {
                        "job_sort": "job.latest_order",
                        "limit": 20,
                        "country": self.WANTED_COUNTRY,
                        "keyword": role,
                    }
                    if config.career_level == "신입":
                        params["years"] = -1
                    response = client.get(self.WANTED_URL, params=params)
                    response.raise_for_status()
                    payload = response.json()
                    jobs = payload.get("data") or payload.get("jobs") or []
                except Exception as exc:
                    self.logger.warning("Wanted 요청 실패(role=%s): %s", role or "*", exc)
                    continue

                for item in jobs:
                    company = ((item.get("company") or {}).get("name") or "").strip()
                    title = (item.get("position") or item.get("title") or "").strip()
                    if not title:
                        continue  # 제목 없는 항목 제외
                    job_id = item.get("id")
                    requirement = self._strip_html(
                        ((item.get("detail") or {}).get("requirement"))
                        or item.get("requirement")
                        or ""
                    )
                    deadline, is_expired = self._parse_deadline(item.get("due_time"))
                    source_url = f"https://www.wanted.co.kr/wd/{job_id}" if job_id else self.WANTED_REFERER

                    candidates.append(
                        PostingCandidate(
                            company=company,
                            role=title,
                            deadline=deadline,
                            is_expired=is_expired,
                            requirements_raw=requirement,
                            source_url=source_url,
                            source="wanted",
                            passed=True,
                        )
                    )

        return candidates

    def _fetch_saramin(self, config: FilterConfig) -> List[PostingCandidate]:
        headers = {
            "User-Agent": self.USER_AGENT,
            "Referer": "https://www.saramin.co.kr/",
        }
        candidates: List[PostingCandidate] = []

        with httpx.Client(headers=headers, timeout=20.0, follow_redirects=True) as client:
            for company, role in self._build_search_pairs(config):
                query = " ".join(part for part in [company, role] if part).strip()
                try:
                    params = {
                        "searchType": "search",
                        "searchword": query,
                        "recruitPageCount": 20,
                    }
                    if config.career_level == "신입":
                        params["career_type"] = "1,3"
                    response = client.get(self.SARAMIN_URL, params=params)
                    response.raise_for_status()
                    page_candidates = self._parse_saramin_html(response.text)
                    candidates.extend(page_candidates)
                except Exception as exc:
                    self.logger.warning("Saramin 요청 실패(query=%s): %s", query or "*", exc)
                    continue

        return candidates

    def _parse_saramin_html(self, html: str) -> List[PostingCandidate]:
        soup = BeautifulSoup(html, "html.parser")
        items = soup.select("div.item_recruit")
        if not items:
            self.logger.warning("Saramin HTML 파싱 실패: item_recruit 없음")
            return []

        candidates: List[PostingCandidate] = []
        for item in items:
            company = self._text_of(item.select_one(".corp_name a, .corp_name"))
            title_node = item.select_one(".job_tit a")
            role = self._text_of(title_node)
            condition = self._text_of(item.select_one(".job_condition"))
            deadline_text = self._text_of(item.select_one(".date"))
            deadline, is_expired = self._parse_deadline(deadline_text)

            link_node = title_node if title_node and getattr(title_node, "name", "") == "a" else None
            if link_node is None and title_node is not None:
                link_node = title_node.select_one("a")
            href = link_node.get("href") if link_node else ""
            source_url = urljoin("https://www.saramin.co.kr", href) if href else self.SARAMIN_URL

            candidates.append(
                PostingCandidate(
                    company=company,
                    role=role,
                    deadline=deadline,
                    is_expired=is_expired,
                    requirements_raw=condition,
                    source_url=source_url,
                    source="saramin",
                    passed=True,
                )
            )

        return candidates

    def _fetch_samsung(self, config: FilterConfig) -> List[PostingCandidate]:
        del config

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.logger.warning("playwright 미설치 - samsung 수집 건너뜀")
            return []

        candidates: List[PostingCandidate] = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(user_agent=self.USER_AGENT)

            try:
                page.goto(self.SAMSUNG_URL, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(5000)

                info_nodes = page.locator(".info")
                info_count = info_nodes.count()

                for idx in range(info_count):
                    text = info_nodes.nth(idx).inner_text().strip()
                    candidate = self._parse_samsung_text_block(text)
                    if candidate is not None:
                        candidates.append(candidate)

                if not candidates:
                    body_text = page.locator("body").inner_text()
                    candidates = self._parse_samsung_body_text(body_text)
            except Exception as exc:
                self.logger.warning("Samsung 페이지 로드 실패: %s", exc)
            finally:
                browser.close()

        return candidates

    def _parse_samsung_text_block(self, text: str) -> Optional[PostingCandidate]:
        if not text or not text.strip():
            return None

        normalized_lines = [
            re.sub(r"\s+", " ", line).strip()
            for line in text.replace("\xa0", " ").splitlines()
            if line.strip()
        ]
        if len(normalized_lines) < 2:
            return None

        normalized_text = "\n".join(normalized_lines)
        period_match = self.SAMSUNG_PERIOD_RE.search(normalized_text)
        if period_match is None:
            return None

        company = normalized_lines[0]
        role = normalized_lines[1]
        if not company or not role:
            return None
        if "채용" not in role and "모집" not in role:
            return None

        talent_types: List[str] = []
        for keyword in ("신입", "경력", "인턴"):
            if keyword in normalized_text and keyword not in talent_types:
                talent_types.append(keyword)

        deadline, is_expired = self._parse_deadline(period_match.group(2))
        requirement_text = normalized_text[period_match.end():].strip()
        requirement_text = re.sub(r"^D-\s*\d+\s*", "", requirement_text)
        requirement_text = re.sub(r"\s+", " ", requirement_text).strip()

        requirement_parts = []
        if talent_types:
            requirement_parts.append(" / ".join(talent_types))
        if requirement_text:
            requirement_parts.append(requirement_text)

        return PostingCandidate(
            company=company,
            role=role,
            deadline=deadline,
            is_expired=is_expired,
            requirements_raw=" | ".join(requirement_parts),
            source_url=self.SAMSUNG_URL,
            source="samsung",
            passed=True,
        )

    def _parse_samsung_body_text(self, body_text: str) -> List[PostingCandidate]:
        if not body_text or not body_text.strip():
            return []

        candidates: List[PostingCandidate] = []
        blocks = [
            block.strip()
            for block in re.split(r"\n\s*\n+", body_text.replace("\xa0", " "))
            if block.strip()
        ]
        for block in blocks:
            candidate = self._parse_samsung_text_block(block)
            if candidate is not None:
                candidates.append(candidate)

        if candidates:
            return candidates

        lines = [
            re.sub(r"\s+", " ", line).strip()
            for line in body_text.replace("\xa0", " ").splitlines()
            if line.strip()
        ]
        for idx, line in enumerate(lines):
            if self.SAMSUNG_PERIOD_RE.search(line) is None:
                continue
            start = max(0, idx - 2)
            end = min(len(lines), idx + 3)
            candidate = self._parse_samsung_text_block("\n".join(lines[start:end]))
            if candidate is not None:
                candidates.append(candidate)

        return candidates

    def _apply_filter(self, candidate: PostingCandidate, config: FilterConfig) -> None:
        flags: List[str] = []
        requirement_text = candidate.requirements_raw.casefold()

        # companies: 검색 쿼리용 / filter_companies: 후처리 필터용
        filter_cos = config.filter_companies or config.companies
        if filter_cos:
            company_lower = candidate.company.casefold()
            if not any(c.casefold() in company_lower for c in filter_cos):
                flags.append("company_mismatch")

        for keyword in config.exclude_keywords:
            if keyword and keyword.casefold() in requirement_text:
                flags.append(f"exclude:{keyword}")

        if config.include_keywords:
            include_matched = any(
                keyword and keyword.casefold() in requirement_text
                for keyword in config.include_keywords
            )
            if not include_matched:
                flags.append("include_keywords_missing")

        if config.deadline_active_only and candidate.is_expired:
            flags.append("expired")

        if config.career_level == "신입" and self._is_entry_only_excluded(candidate.requirements_raw):
            flags.append("career_only")

        candidate.filter_flags = flags
        candidate.passed = not flags

    def _is_entry_only_excluded(self, requirements_raw: str) -> bool:
        text = requirements_raw.casefold()
        return "경력" in text and "신입" not in text and "경력무관" not in text

    def _build_search_pairs(self, config: FilterConfig) -> List[Tuple[str, str]]:
        companies = config.companies or [""]
        roles = config.roles or [""]
        return list(product(companies, roles))

    def _deduplicate(self, candidates: Iterable[PostingCandidate]) -> Iterable[PostingCandidate]:
        seen = set()
        for candidate in candidates:
            key = (
                candidate.source,
                candidate.source_url,
                candidate.company,
                candidate.role,
            )
            if key in seen:
                continue
            seen.add(key)
            yield candidate

    def _parse_deadline(self, raw_value: object) -> Tuple[str, bool]:
        if raw_value in (None, ""):
            return "상시", False

        if isinstance(raw_value, (int, float)):
            timestamp = float(raw_value)
            if timestamp > 10**12:
                timestamp /= 1000.0
            parsed = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            return parsed.date().isoformat(), parsed < datetime.now(timezone.utc)

        text = str(raw_value).strip()
        if not text:
            return "상시", False
        if any(token in text for token in ["상시", "채용시", "미정"]):
            return "상시", False

        parsed = self._parse_datetime_text(text)
        if parsed is not None:
            if parsed.tzinfo is None:
                now = datetime.now()
            else:
                now = datetime.now(parsed.tzinfo)
            return parsed.date().isoformat(), parsed < now

        date_match = re.search(r"(20\d{2})[./-](\d{1,2})[./-](\d{1,2})", text)
        if date_match:
            year, month, day = map(int, date_match.groups())
            parsed_date = datetime(year, month, day)
            return parsed_date.date().isoformat(), parsed_date.date() < datetime.now().date()

        month_day_match = re.search(r"(\d{1,2})[./-](\d{1,2})", text)
        if month_day_match:
            month, day = map(int, month_day_match.groups())
            year = datetime.now().year
            try:
                parsed_date = datetime(year, month, day)
            except ValueError:
                return "미확인", False
            return parsed_date.date().isoformat(), parsed_date.date() < datetime.now().date()

        return "미확인", False

    def _parse_datetime_text(self, value: str) -> Optional[datetime]:
        normalized = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            pass

        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None

    def _strip_html(self, value: str) -> str:
        if "<" not in value:
            return value.strip()
        return BeautifulSoup(value, "html.parser").get_text(" ", strip=True)

    def _text_of(self, node) -> str:
        if node is None:
            return ""
        return node.get_text(" ", strip=True)

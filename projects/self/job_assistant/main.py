"""
Job Assistant — CLI 진입점
채용공고 분석 + 자소서 매칭 시스템

Usage:
  python main.py --company 카카오 --role "백엔드 엔지니어"
  python main.py --company 네이버 --role "데이터 분석가" --url https://...
  python main.py --company 에이브랩스 --role "Decision Scientist" --no-search
"""
import argparse
import json
import os
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.dirname(__file__))

from config import API_CONFIG, COVER_LETTERS_DIR, DATA_DIR, OUTPUTS_DIR
from core.message_bus import JobContext
from agents.search_agent import SearchAgent
from agents.analyzer_agent import AnalyzerAgent
from agents.writer_agent import WriterAgent
from agents.collector_agent import CollectorAgent
from agents.summarizer_agent import SummarizerAgent
from agents.notebook_publisher import NotebookPublisher

# 사용 가능한 파이프라인 단계
# collect  : CollectorAgent — 4카테고리 Perplexity 수집
# summarize: SummarizerAgent — OpenAI/Gemini/Claude 요약
# notebook : NotebookPublisher — 소스 파일 저장 + 업로드 가이드
# analyze  : AnalyzerAgent — Claude 구조화 분석
# write    : WriterAgent — 자소서 초안
ALL_STEPS = ["collect", "summarize", "notebook", "analyze", "write"]

import uuid
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)


def load_cover_letters(directory: str) -> dict:
    """data/cover_letters/ 에서 .md, .txt 파일 로드"""
    cover_letters = {}
    dir_path = Path(directory)
    if not dir_path.exists():
        return cover_letters

    for ext in ("*.md", "*.txt"):
        for filepath in dir_path.glob(ext):
            try:
                content = filepath.read_text(encoding="utf-8")
                cover_letters[filepath.name] = content
                print(f"  자소서 로드: {filepath.name} ({len(content)} chars)")
            except Exception as e:
                print(f"  자소서 로드 실패: {filepath.name} — {e}")

    return cover_letters


def print_result(result, verbose: bool = False):
    """결과 출력"""
    print("\n" + "=" * 60)
    print(f"  {result.company} — {result.role}")
    print("=" * 60)

    for i, section in enumerate(result.sections, 1):
        print(f"\n[{i}] {section.title}")
        print("-" * 40)

        if section.source:
            preview = section.source[:200].replace("\n", " ")
            print(f"  재사용 소스: {preview}{'...' if len(section.source) > 200 else ''}")

        if section.tailored:
            print(f"  조정 방향: {section.tailored[:300]}")

        if section.gap:
            print(f"  GAP (추가필요): {section.gap[:200]}")
            if section.task_file:
                print(f"  Task 저장: {section.task_file}")

    if result.has_gaps():
        print(f"\n  pending tasks: {len(result.pending_tasks())}개")
        print("  → data/tasks/pending/ 에서 Codex로 처리 가능")

    print("\n" + "=" * 60)


def save_analysis(analysis, output_dir: str) -> str:
    """AnalyzerAgent 분석 결과를 JSON으로 저장 (eco_system_v2 연동용)"""
    os.makedirs(output_dir, exist_ok=True)
    from datetime import date
    filename = f"{analysis.posting.company}_{analysis.posting.role}_{date.today()}_analysis.json"
    filepath = os.path.join(output_dir, filename)

    data = {
        "company": analysis.posting.company,
        "role": analysis.posting.role,
        "vision": analysis.posting.vision,
        "recent_work": analysis.posting.recent_work,
        "key_competencies": analysis.key_competencies,
        "technical_skills": analysis.technical_skills,
        "soft_skills": analysis.soft_skills,
        "culture_fit": analysis.culture_fit,
        "keywords": analysis.keywords,
        "cover_letter_sections": analysis.cover_letter_sections,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  분석 저장: {filepath}")
    return filepath


def save_result(result, output_dir: str):
    """결과를 JSON으로 저장"""
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{result.company}_{result.role}_{result.created_at[:10]}.json"
    filepath = os.path.join(output_dir, filename)

    data = {
        "company": result.company,
        "role": result.role,
        "created_at": result.created_at,
        "cover_letters_used": result.cover_letters_used,
        "sections": [
            {
                "title": s.title,
                "source": s.source,
                "tailored": s.tailored,
                "gap": s.gap,
                "task_file": s.task_file,
            }
            for s in result.sections
        ],
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n  결과 저장: {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(
        prog="job-assistant",
        description="채용공고 분석 + 자소서 매칭 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python main.py --company 카카오 --role "백엔드 엔지니어"
  python main.py --company 네이버 --role "데이터 분석가" --url https://...
  python main.py --company 에이브랩스 --role "Decision Scientist" --no-search
  python main.py --check-env
        """,
    )

    parser.add_argument("--company", "-c", type=str, help="기업명")
    parser.add_argument("--role", "-r", type=str, help="직무명")
    parser.add_argument("--url", "-u", type=str, default="", help="채용공고 URL (선택)")
    parser.add_argument("--discover", action="store_true", help="공고 탐색 모드")
    parser.add_argument("--match", action="store_true", help="프로필 기반 공고 탐색")
    parser.add_argument(
        "--exclude",
        nargs="+",
        default=[],
        help="제외 키워드 (예: '토익스피킹 160' '이공계')",
    )
    parser.add_argument("--include-kw", nargs="+", default=[], help="포함 키워드")
    parser.add_argument(
        "--cover-letters-dir",
        type=str,
        default=COVER_LETTERS_DIR,
        help=f"자소서 디렉토리 (기본: {COVER_LETTERS_DIR})",
    )
    parser.add_argument(
        "--steps", "-s",
        type=str,
        default="collect,summarize,notebook,analyze,write",
        help=(
            "실행할 단계 (쉼표 구분). "
            f"가능: {', '.join(ALL_STEPS)} / all (기본: 전체)"
        ),
    )
    parser.add_argument(
        "--no-search",
        action="store_true",
        help="Perplexity 검색 건너뜀 (기존 raw_search 사용, 레거시)",
    )
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="API 키 환경변수 확인",
    )
    parser.add_argument(
        "--profile-file",
        type=str,
        default=os.path.join("data", "profile.md"),
        help="프로필 파일 경로 (기본: data/profile.md)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="상세 출력"
    )

    args = parser.parse_args()

    # --check-env
    if args.check_env:
        status = API_CONFIG.validate()
        print("API 키 상태:")
        for name, ok in status.items():
            mark = "OK" if ok else "MISSING"
            print(f"  {name}: {mark}")
        sys.exit(0)

    if args.match:
        from agents.discovery_agent import DiscoveryAgent
        from agents.profile_analyzer import ProfileAnalyzer
        from core.models import FilterConfig

        if not API_CONFIG.anthropic_key:
            print("\nERROR: API 키 누락: anthropic\nexport ANTHROPIC_API_KEY=...")
            sys.exit(1)

        profile_path = args.profile_file
        if not os.path.isabs(profile_path):
            profile_path = os.path.join(os.path.dirname(__file__), profile_path)

        if not os.path.exists(profile_path):
            fallback_path = os.path.join(DATA_DIR, "profile.md")
            print(f"\nERROR: 프로필 파일이 없습니다: {profile_path}")
            print(f"기본 위치: {fallback_path}")
            sys.exit(1)

        analyzer = ProfileAnalyzer()
        search_config = analyzer.analyze(profile_path)

        print("\n프로필 분석 완료:")
        print(f"  직무 키워드: {search_config.role_keywords}")
        print(f"  탐색 기업: {search_config.target_companies}")

        all_candidates = []
        agent = DiscoveryAgent()

        # Samsung은 1회만 수집 (Playwright 비용)
        print("  Samsung 공고 수집 중...")
        samsung_pool = agent.fetch_samsung_once()
        print(f"  Samsung {len(samsung_pool)}개 수집 완료")

        # 직무 키워드 검색 (상위 5개)
        # companies는 검색 쿼리에 넣지 않고 filter_companies로 후처리 필터만 적용
        top_roles = search_config.role_keywords[:5]
        for i, role in enumerate(top_roles):
            print(f"  [{i+1}/{len(top_roles)}] '{role}' 검색 중...")
            config = FilterConfig(
                roles=[role],
                exclude_keywords=search_config.exclude_requirements,
                career_level=search_config.career_level,
                deadline_active_only=True,
            )
            # Samsung은 첫 번째에만 주입
            sc = samsung_pool if i == 0 else []
            all_candidates.extend(agent.run(config, samsung_candidates=sc))

        # 중복 제거 (회사+공고제목 기준)
        seen = set()
        unique = []
        for candidate in all_candidates:
            key = (candidate.company, candidate.role[:40])
            if key not in seen:
                seen.add(key)
                unique.append(candidate)

        passed = [c for c in unique if c.passed]
        # 타겟 기업 우선 → 마감일 순 정렬
        target_set = {t.casefold() for t in search_config.target_companies}
        def sort_key(c):
            is_target = any(t in c.company.casefold() for t in target_set)
            return (not is_target, c.deadline)

        print(f"\n통과 공고: {len(passed)}개\n")
        for c in sorted(passed, key=sort_key):
            tag = "★" if any(t in c.company.casefold() for t in target_set) else " "
            print(f"{tag}[{c.source}] {c.company} — {c.role[:60]}")
            print(f"  마감: {c.deadline} | {c.source_url}")
        sys.exit(0)

    if args.discover:
        from agents.discovery_agent import DiscoveryAgent
        from core.models import FilterConfig

        config = FilterConfig(
            companies=[args.company] if args.company else [],
            roles=[args.role] if args.role else [],
            exclude_keywords=args.exclude,
            include_keywords=args.include_kw,
        )
        agent = DiscoveryAgent()
        candidates = agent.run(config)

        passed = [c for c in candidates if c.passed]
        filtered = [c for c in candidates if not c.passed]
        print(f"\n통과 공고: {len(passed)}개 / 제외: {len(filtered)}개\n")
        for c in passed:
            print(f"  [{c.source}] {c.company} — {c.role}")
            print(f"    마감: {c.deadline} | URL: {c.source_url}")
        sys.exit(0)

    if not args.company or not args.role:
        parser.print_help()
        sys.exit(1)

    # API 키 검증
    try:
        API_CONFIG.check_required()
    except EnvironmentError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

    # 자소서 로드
    print(f"\n자소서 로드 중: {args.cover_letters_dir}")
    cover_letters = load_cover_letters(args.cover_letters_dir)
    if not cover_letters:
        print("  (자소서 없음 — writer는 gap만 생성합니다)")

    # 컨텍스트 초기화
    context = JobContext(
        task_id=str(uuid.uuid4())[:8],
        company=args.company,
        role=args.role,
        url=args.url,
        cover_letters_raw=cover_letters,
    )

    print(f"\n작업 시작 | task_id={context.task_id}")
    print(f"  대상: {args.company} / {args.role}")

    # 실행 단계 파싱
    steps_input = args.steps.lower()
    if steps_input == "all":
        steps = set(ALL_STEPS)
    else:
        steps = set(s.strip() for s in steps_input.split(","))

    print(f"  실행 단계: {', '.join(s for s in ALL_STEPS if s in steps)}")

    # 파이프라인 실행
    total = len([s for s in ALL_STEPS if s in steps])
    current = 0

    try:
        # [collect] CollectorAgent — 4카테고리 수집
        if "collect" in steps:
            current += 1
            print(f"\n[{current}/{total}] CollectorAgent — 멀티카테고리 수집")
            collector = CollectorAgent()
            collector.run(context)

        # 레거시 호환: collect 없이 search만 지정한 경우
        elif not args.no_search and "analyze" in steps:
            current += 1
            print(f"\n[{current}/{total}] SearchAgent (레거시) — Perplexity 검색")
            search_agent = SearchAgent()
            search_agent.run(context)

        # [summarize] SummarizerAgent — 멀티모델 요약
        if "summarize" in steps and context.collected_content:
            current += 1
            print(f"\n[{current}/{total}] SummarizerAgent — 멀티모델 요약")
            summarizer = SummarizerAgent()
            summarizer.run(context)

        # [notebook] NotebookPublisher — 소스 저장 + 업로드 가이드
        if "notebook" in steps and context.summarized_sources:
            current += 1
            print(f"\n[{current}/{total}] NotebookPublisher — 소스 파일 생성")
            publisher = NotebookPublisher()
            publisher.run(context)

        # [analyze] AnalyzerAgent — 구조화 분석
        if "analyze" in steps:
            # collected_content → job_posting 변환 (collect 결과 활용)
            if context.collected_content and not context.job_posting:
                from core.models import JobPosting
                jd_raw = context.collected_content.raw.get("JD", "")
                context.job_posting = JobPosting(
                    company=context.company,
                    role=context.role,
                    vision="",
                    jd=jd_raw,
                    requirements=[],
                    preferred=[],
                    recent_work="",
                    raw_search=jd_raw,
                )

            if context.job_posting:
                current += 1
                print(f"\n[{current}/{total}] AnalyzerAgent — Claude 분석")
                analyzer = AnalyzerAgent()
                analyzer.run(context)
                if context.analysis:
                    save_analysis(context.analysis, OUTPUTS_DIR)
            else:
                print(f"\n[{current}/{total}] AnalyzerAgent — JobPosting 없음, 건너뜀")

        # [write] WriterAgent — 자소서 초안
        if "write" in steps and context.analysis:
            current += 1
            print(f"\n[{current}/{total}] WriterAgent — 자소서 매핑")
            writer = WriterAgent()
            result = writer.run(context)
            print_result(result, verbose=args.verbose)
            save_result(result, OUTPUTS_DIR)
        elif "write" in steps:
            print(f"\n[write] WriterAgent — Analysis 없음, 건너뜀")

    except KeyboardInterrupt:
        print("\n\n중단됨")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

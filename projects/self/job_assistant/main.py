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

from config import API_CONFIG, COVER_LETTERS_DIR, OUTPUTS_DIR
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

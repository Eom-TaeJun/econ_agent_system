"""
NotebookPublisher — 소스 파일 생성 + NotebookLM 업로드 가이드 출력

Python에서 NotebookLM API 직접 호출 불가 (MCP 기반).
따라서:
  1. 소스 텍스트를 data/notebooks/{company}_{role}/ 에 저장
  2. Claude Code(MCP)에서 업로드할 수 있도록 업로드 가이드 출력
  3. notebook_id가 주어지면 context에 저장
"""
import os
import json
from datetime import datetime
from typing import List

from agents.base_agent import BaseAgent
from config import OUTPUTS_DIR
from core.message_bus import JobContext, MessageType
from core.models import NotebookResult, SummarizedSource


NOTEBOOKS_DIR = os.path.join(OUTPUTS_DIR, "notebooks")


class NotebookPublisher(BaseAgent):
    """소스 파일 저장 + MCP 업로드 가이드 출력"""

    def __init__(self):
        super().__init__("NotebookPublisher")

    def _setup_client(self):
        pass  # MCP 경유 → Python 클라이언트 불필요

    def run(self, context: JobContext) -> NotebookResult:
        self.log_progress(f"노트북 소스 생성: {context.company} / {context.role}")

        sources: List[SummarizedSource] = getattr(context, "summarized_sources", [])
        if not sources:
            raise ValueError("SummarizedSource 없음. SummarizerAgent를 먼저 실행하세요.")

        # 저장 디렉토리 생성
        safe_name = f"{context.company}_{context.role}".replace(" ", "_").replace("/", "-")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        output_dir = os.path.join(NOTEBOOKS_DIR, f"{safe_name}_{timestamp}")
        os.makedirs(output_dir, exist_ok=True)

        # 소스 파일 저장
        saved_files = []
        for i, source in enumerate(sources, 1):
            filename = f"{i:02d}_{source.category}_{source.model_used}.md"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# {source.title}\n\n")
                f.write(source.content)
            saved_files.append(filepath)
            self.log_progress(f"  저장: {filename}")

        # 메타데이터 저장
        meta = {
            "company": context.company,
            "role": context.role,
            "created_at": timestamp,
            "sources": [
                {
                    "title": s.title,
                    "category": s.category,
                    "model_used": s.model_used,
                    "char_count": len(s.content),
                }
                for s in sources
            ],
        }
        meta_path = os.path.join(output_dir, "_meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        # 업로드 가이드 출력
        self._print_upload_guide(context, sources, output_dir)

        result = NotebookResult(
            company=context.company,
            role=context.role,
            sources=sources,
            output_dir=output_dir,
        )
        context.notebook_result = result

        context.add_message(
            sender="NotebookPublisher",
            receiver="user",
            content={"output_dir": output_dir, "source_count": len(sources)},
            msg_type=MessageType.RESULT,
        )

        self.log_success(f"소스 {len(sources)}개 저장 완료: {output_dir}")
        return result

    def _print_upload_guide(
        self,
        context: JobContext,
        sources: List[SummarizedSource],
        output_dir: str,
    ) -> None:
        notebook_title = f"{context.company} {context.role} — 지원 전략 분석"

        print("\n" + "=" * 60)
        print("  NotebookLM 업로드 가이드")
        print("=" * 60)
        print(f"\n  노트북 제목: {notebook_title}")
        print(f"  소스 파일 위치: {output_dir}\n")
        print("  Claude Code에서 다음 명령으로 업로드 가능:")
        print("  (MCP notebooklm 도구 사용)\n")
        print("  1. 노트북 생성:")
        print(f'     mcp__notebooklm__create_notebook(title="{notebook_title}")\n')
        print("  2. 소스 추가 (notebook_id 채워서 실행):")
        for i, source in enumerate(sources, 1):
            filename = f"{i:02d}_{source.category}_{source.model_used}.md"
            print(f"     [{i}] {source.title}")
            print(f"         파일: {filename}")
        print("\n" + "=" * 60)

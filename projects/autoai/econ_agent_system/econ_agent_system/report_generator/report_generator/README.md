# 📊 Multi-Agent Report Generator

JSON 기반 다중 에이전트 분석 결과를 전문적인 한/영 양국어 보고서로 자동 변환합니다.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Report Generation Flow                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   JSON Output     Section Writers          Document Builder          │
│   ┌─────────┐    ┌─────────────────┐      ┌──────────────┐         │
│   │ Multi-  │    │   Claude        │      │              │         │
│   │ Agent   │───►│   (Anthropic)   │─────►│    docx-js   │───► DOCX│
│   │ System  │    │   - Methodology │      │   (Node.js)  │         │
│   │         │    │   - Results     │      │              │         │
│   │ outputs/│    │   - Discussion  │      │  Bilingual   │         │
│   │ project_│    ├─────────────────┤      │  Professional│         │
│   │ xxx.json│    │   GPT-4         │      │  Formatting  │         │
│   │         │───►│   (OpenAI)      │─────►│              │         │
│   └─────────┘    │   - Exec Summary│      └──────────────┘         │
│                  │   - Introduction│                                │
│                  │   - Conclusion  │                                │
│                  └─────────────────┘                                │
└─────────────────────────────────────────────────────────────────────┘
```

## 📋 Agent Roles (에이전트 역할)

| Agent | Role | Sections |
|-------|------|----------|
| **Claude** (Anthropic) | 상세 분석 | Methodology, Results, Discussion |
| **GPT-4** (OpenAI) | 요약 및 구조화 | Executive Summary, Introduction, Conclusion |

## 🚀 Quick Start

### 1. Prerequisites (필수 요구사항)

```bash
# Python packages
pip install anthropic openai

# Node.js (for DOCX generation)
# https://nodejs.org/

# docx package (auto-installed on first run)
npm install docx
```

### 2. Environment Variables (환경 변수)

```bash
export ANTHROPIC_API_KEY="your-anthropic-key"
export OPENAI_API_KEY="your-openai-key"
```

### 3. Generate Report (보고서 생성)

```bash
# Full bilingual report
python generate_report.py outputs/project_45ffab5c.json

# With custom output name
python generate_report.py project.json --output my_analysis_report

# Preview JSON structure first
python generate_report.py project.json --preview

# Korean-only report
python generate_report.py project.json --korean-only

# English-only report  
python generate_report.py project.json --english-only

# Check dependencies
python generate_report.py --check
```

## 📁 Output Structure (출력 구조)

```
report_sections_[task_id].json   # Intermediate sections (for debugging)
report_[task_id].docx            # Final bilingual report
```

### DOCX Report Structure (보고서 구조)

```
1. Cover Page (표지)
   - Title / 제목
   - Task ID
   - Generation Date
   - Agent Credits

2. Table of Contents (목차)

3. Executive Summary / 요약
   🇰🇷 한국어
   🇺🇸 English

4. Introduction / 서론
   🇰🇷 한국어
   🇺🇸 English

5. Methodology / 방법론
   🇰🇷 한국어
   🇺🇸 English

6. Results / 결과
   🇰🇷 한국어
   🇺🇸 English

7. Discussion / 논의
   🇰🇷 한국어
   🇺🇸 English

8. Conclusion / 결론
   🇰🇷 한국어
   🇺🇸 English
```

## 🔌 Integration with Multi-Agent System

### Option 1: Standalone Usage (독립 사용)

기존 시스템에서 생성된 JSON 파일을 직접 변환:

```bash
# After running your multi-agent analysis
python main.py --query "Analyze Bitcoin and macro indicators" --auto

# Generate report from output
python generate_report.py outputs/project_xxx.json
```

### Option 2: Integrated Workflow (통합 워크플로우)

`main.py`에 자동 보고서 생성 추가:

```python
# main.py에 추가
from report_generator.generate_report import generate_sections, build_document

async def run_direct(query: str, auto_mode: bool = False, template: str = None):
    # ... existing code ...
    
    result = await orchestrator.run_project(query, auto_mode=auto_mode)
    
    # Save results
    output_file = f"outputs/project_{result['task_id']}.json"
    os.makedirs('outputs', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=str, ensure_ascii=False)
    
    # ✨ Auto-generate report
    if auto_mode:
        print("\n📊 Generating report...")
        report_result = await generate_sections(output_file)
        sections_file = f"report_sections_{result['task_id']}.json"
        with open(sections_file, 'w', encoding='utf-8') as f:
            json.dump(report_result, f, indent=2, ensure_ascii=False)
        build_document(sections_file, f"report_{result['task_id']}")
    
    return result
```

### Option 3: As a New Agent (새 에이전트로 추가)

`agents/report_generator.py` 생성:

```python
# agents/report_generator.py
from report_generator.report_agent import ReportOrchestrator

class ReportGeneratorAgent:
    """Report generation agent for the multi-agent system"""
    
    def __init__(self):
        self.orchestrator = ReportOrchestrator()
    
    async def generate(self, json_path: str):
        return await self.orchestrator.generate_report(json_path)
```

## 📊 Expected JSON Format (예상 JSON 형식)

```json
{
  "task_id": "45ffab5c",
  "query": "Analyze Bitcoin and macro-financial indicators...",
  "plan": {
    "project_title": "Bitcoin Macro Economic Analysis",
    "objective": "To analyze the relationship...",
    "phases": [...],
    "success_criteria": [...],
    "potential_variables": [...]
  },
  "results": {
    "phase_1": { "name": "Research", "agent": "perplexity", "result": {...} },
    "phase_2": { "name": "Data Collection", "agent": "gemini", "result": {...} },
    "phase_3": { "name": "Analysis", "agent": "claude", "result": {...} }
  },
  "final_output": {
    "synthesis": "...",
    "generated_at": "2025-11-28T22:57:05"
  }
}
```

## 🛠️ Customization (커스터마이징)

### Custom Sections (섹션 추가)

`report_agent.py`의 `ReportOrchestrator.generate_report()` 수정:

```python
# Add custom section
self.sections['custom_section'] = await self.claude_writer.write_section(
    'custom', {'data': your_custom_data}
)
```

### Custom Styling (스타일 변경)

`document_builder.js`의 `STYLES` 수정:

```javascript
const STYLES = {
    paragraphStyles: [
        {
            id: "Heading1",
            run: { size: 36, bold: true, color: "YOUR_COLOR" },
            // ...
        }
    ]
};
```

## 📝 API Costs Estimate (API 비용 예상)

Per report generation (보고서 1건당):
- Claude: ~$0.10-0.20 (6 sections × ~1000 tokens each)
- GPT-4: ~$0.05-0.10 (3 sections × ~800 tokens each)
- **Total: ~$0.15-0.30 per report**

## 🐛 Troubleshooting

### "docx is not installed"
```bash
npm install docx
# or globally
npm install -g docx
```

### "API key not found"
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
```

### "Korean text rendering issues"
DOCX uses Arial font which supports Korean. If issues persist, install Korean fonts on your system.

## 📄 License

MIT License - Feel free to modify and distribute.

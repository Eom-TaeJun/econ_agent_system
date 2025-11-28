#!/usr/bin/env python3
"""
Report Generator Agent
======================
Converts Multi-Agent System JSON outputs into professional bilingual reports.

Agents:
- Claude: Detailed analysis sections (Methodology, Results)
- GPT-4: Summary sections (Executive Summary, Conclusion)

Output: Bilingual DOCX report (Korean + English)
"""

import json
import asyncio
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from abc import ABC, abstractmethod

# API Clients
import anthropic
import openai


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class ProjectPlan:
    """Parsed project plan from JSON"""
    title: str
    objective: str
    phases: List[Dict]
    success_criteria: List[str]
    potential_variables: List[str]
    estimated_time: str


@dataclass
class PhaseResult:
    """Result from a single phase"""
    phase_number: int
    name: str
    agent: str
    tasks_completed: int
    results: List[Dict]


@dataclass
class ParsedReport:
    """Fully parsed JSON report"""
    task_id: str
    query: str
    plan: ProjectPlan
    phase_results: List[PhaseResult]
    synthesis: str
    generated_at: str
    raw_data: Dict  # Original JSON for reference


# ============================================================================
# JSON Parser
# ============================================================================

class JSONReportParser:
    """Parses Multi-Agent System JSON output into structured data"""
    
    def parse(self, json_path: str) -> ParsedReport:
        """Parse JSON file into ParsedReport"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Parse plan
        plan_data = data.get('plan', {})
        plan = ProjectPlan(
            title=plan_data.get('project_title', 'Untitled Project'),
            objective=plan_data.get('objective', ''),
            phases=plan_data.get('phases', []),
            success_criteria=plan_data.get('success_criteria', []),
            potential_variables=plan_data.get('potential_variables', []),
            estimated_time=plan_data.get('estimated_time', 'N/A')
        )
        
        # Parse phase results
        phase_results = []
        results_data = data.get('results', {})
        
        for phase_key in sorted(results_data.keys()):
            phase_data = results_data[phase_key]
            if isinstance(phase_data, dict):
                result_content = phase_data.get('result', {})
                phase_results.append(PhaseResult(
                    phase_number=int(phase_key.split('_')[1]),
                    name=phase_data.get('name', ''),
                    agent=phase_data.get('agent', ''),
                    tasks_completed=result_content.get('tasks_completed', 0),
                    results=result_content.get('results', [])
                ))
        
        # Parse final output
        final_output = data.get('final_output', {})
        
        return ParsedReport(
            task_id=data.get('task_id', ''),
            query=data.get('query', ''),
            plan=plan,
            phase_results=phase_results,
            synthesis=final_output.get('synthesis', ''),
            generated_at=final_output.get('generated_at', ''),
            raw_data=data
        )
    
    def extract_key_findings(self, report: ParsedReport) -> Dict[str, List[str]]:
        """Extract key findings from each phase"""
        findings = {}
        
        for phase in report.phase_results:
            phase_findings = []
            for result in phase.results:
                content = result.get('content', '')
                # Extract first few sentences as key points
                if content:
                    sentences = content.split('.')[:3]
                    phase_findings.append('. '.join(sentences) + '.')
            findings[f"{phase.name} ({phase.agent})"] = phase_findings
        
        return findings


# ============================================================================
# LLM Section Writers
# ============================================================================

class SectionWriter(ABC):
    """Abstract base class for section writers"""
    
    @abstractmethod
    async def write_section(self, section_type: str, context: Dict) -> Dict[str, str]:
        """Write a report section in both languages"""
        pass


class ClaudeSectionWriter(SectionWriter):
    """Claude handles detailed analysis sections"""
    
    def __init__(self, api_key: str = None):
        self.client = anthropic.Anthropic(api_key=api_key or os.getenv('ANTHROPIC_API_KEY'))
        self.model = "claude-sonnet-4-20250514"
    
    async def write_section(self, section_type: str, context: Dict) -> Dict[str, str]:
        """Generate section content in both Korean and English"""
        
        prompts = {
            'methodology': self._methodology_prompt,
            'results': self._results_prompt,
            'discussion': self._discussion_prompt,
        }
        
        prompt_fn = prompts.get(section_type, self._generic_prompt)
        prompt = prompt_fn(context)
        
        # Generate Korean version
        korean_response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": f"{prompt}\n\n반드시 한국어로 작성해주세요. 학술적이고 전문적인 톤을 유지하세요."
            }]
        )
        
        # Generate English version
        english_response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": f"{prompt}\n\nWrite in English. Maintain an academic and professional tone."
            }]
        )
        
        return {
            'korean': korean_response.content[0].text,
            'english': english_response.content[0].text
        }
    
    def _methodology_prompt(self, context: Dict) -> str:
        return f"""Based on the following project information, write a detailed Methodology section:

Project Title: {context.get('title', '')}
Objective: {context.get('objective', '')}

Analysis Phases:
{json.dumps(context.get('phases', []), indent=2, ensure_ascii=False)}

Variables Analyzed:
{', '.join(context.get('variables', []))}

Write a comprehensive methodology section that explains:
1. The multi-agent approach used
2. Each analysis phase and its purpose
3. Data sources and variables
4. Analytical methods employed"""

    def _results_prompt(self, context: Dict) -> str:
        return f"""Based on the following analysis results, write a detailed Results section:

Phase Results:
{json.dumps(context.get('phase_results', []), indent=2, ensure_ascii=False, default=str)[:8000]}

Synthesize the findings and present:
1. Key findings from each phase
2. Statistical results (if any)
3. Notable patterns or relationships discovered
4. Agent contributions and their outputs"""

    def _discussion_prompt(self, context: Dict) -> str:
        return f"""Based on the following findings, write a Discussion section:

Project Objective: {context.get('objective', '')}
Key Findings: {context.get('findings', '')}
Synthesis: {context.get('synthesis', '')[:3000]}

Discuss:
1. Interpretation of results in economic/financial context
2. Implications of the findings
3. Limitations of the analysis
4. Comparison with existing literature (if applicable)"""

    def _generic_prompt(self, context: Dict) -> str:
        return f"""Write a report section based on: {json.dumps(context, indent=2, ensure_ascii=False, default=str)[:5000]}"""


class GPTSectionWriter(SectionWriter):
    """GPT handles summary and structural sections"""
    
    def __init__(self, api_key: str = None):
        self.client = openai.OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4o"
    
    async def write_section(self, section_type: str, context: Dict) -> Dict[str, str]:
        """Generate section content in both Korean and English"""
        
        prompts = {
            'executive_summary': self._executive_summary_prompt,
            'introduction': self._introduction_prompt,
            'conclusion': self._conclusion_prompt,
        }
        
        prompt_fn = prompts.get(section_type, self._generic_prompt)
        prompt = prompt_fn(context)
        
        # Generate Korean version
        korean_response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": f"{prompt}\n\n반드시 한국어로 작성해주세요. 명확하고 간결하게 작성하세요."
            }]
        )
        
        # Generate English version
        english_response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": f"{prompt}\n\nWrite in English. Be clear and concise."
            }]
        )
        
        return {
            'korean': korean_response.choices[0].message.content,
            'english': english_response.choices[0].message.content
        }
    
    def _executive_summary_prompt(self, context: Dict) -> str:
        return f"""Write an Executive Summary for this analysis report:

Project: {context.get('title', '')}
Objective: {context.get('objective', '')}
Key Findings Summary: {context.get('synthesis', '')[:2000]}

The Executive Summary should:
1. State the purpose in 1-2 sentences
2. Highlight 3-5 key findings
3. Present main conclusions
4. Be no longer than 300 words"""

    def _introduction_prompt(self, context: Dict) -> str:
        return f"""Write an Introduction section for this economics/finance analysis report:

Project: {context.get('title', '')}
Research Question/Query: {context.get('query', '')}
Variables: {', '.join(context.get('variables', []))}

The Introduction should:
1. Provide background context
2. State the research question
3. Explain the relevance/importance
4. Outline the report structure"""

    def _conclusion_prompt(self, context: Dict) -> str:
        return f"""Write a Conclusion section for this analysis report:

Project: {context.get('title', '')}
Objective: {context.get('objective', '')}
Synthesis: {context.get('synthesis', '')[:2500]}
Success Criteria: {context.get('success_criteria', [])}

The Conclusion should:
1. Summarize key findings
2. Address whether objectives were met
3. Provide actionable recommendations
4. Suggest future research directions"""

    def _generic_prompt(self, context: Dict) -> str:
        return f"""Write a report section based on: {json.dumps(context, indent=2, ensure_ascii=False, default=str)[:5000]}"""


# ============================================================================
# Report Orchestrator
# ============================================================================

class ReportOrchestrator:
    """Orchestrates the report generation process"""
    
    def __init__(self, anthropic_key: str = None, openai_key: str = None):
        self.parser = JSONReportParser()
        self.claude_writer = ClaudeSectionWriter(anthropic_key)
        self.gpt_writer = GPTSectionWriter(openai_key)
        self.sections: Dict[str, Dict[str, str]] = {}
    
    async def generate_report(self, json_path: str) -> Dict:
        """Generate complete bilingual report from JSON"""
        
        print(f"\n📄 Parsing JSON: {json_path}")
        report = self.parser.parse(json_path)
        findings = self.parser.extract_key_findings(report)
        
        # Prepare contexts for each section
        base_context = {
            'title': report.plan.title,
            'objective': report.plan.objective,
            'query': report.query,
            'variables': report.plan.potential_variables,
            'phases': report.plan.phases,
            'synthesis': report.synthesis,
            'success_criteria': report.plan.success_criteria,
            'findings': findings,
        }
        
        results_context = {
            **base_context,
            'phase_results': [
                {
                    'phase': pr.phase_number,
                    'name': pr.name,
                    'agent': pr.agent,
                    'tasks': pr.tasks_completed,
                    'results': pr.results[:3]  # Limit to avoid token overflow
                }
                for pr in report.phase_results
            ]
        }
        
        # Generate sections with appropriate agents
        print("\n🤖 Generating report sections...")
        
        # GPT: Summary sections
        print("   📝 GPT → Executive Summary...")
        self.sections['executive_summary'] = await self.gpt_writer.write_section(
            'executive_summary', base_context
        )
        
        print("   📝 GPT → Introduction...")
        self.sections['introduction'] = await self.gpt_writer.write_section(
            'introduction', base_context
        )
        
        # Claude: Detailed sections
        print("   📝 Claude → Methodology...")
        self.sections['methodology'] = await self.claude_writer.write_section(
            'methodology', base_context
        )
        
        print("   📝 Claude → Results...")
        self.sections['results'] = await self.claude_writer.write_section(
            'results', results_context
        )
        
        print("   📝 Claude → Discussion...")
        self.sections['discussion'] = await self.claude_writer.write_section(
            'discussion', {**base_context, 'findings': str(findings)}
        )
        
        # GPT: Conclusion
        print("   📝 GPT → Conclusion...")
        self.sections['conclusion'] = await self.gpt_writer.write_section(
            'conclusion', base_context
        )
        
        print("\n✅ All sections generated!")
        
        return {
            'parsed_report': report,
            'sections': self.sections,
            'metadata': {
                'task_id': report.task_id,
                'generated_at': datetime.now().isoformat(),
                'source_file': json_path
            }
        }


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Test the report generator"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python report_agent.py <json_file>")
        print("Example: python report_agent.py outputs/project_45ffab5c.json")
        return
    
    json_path = sys.argv[1]
    
    if not os.path.exists(json_path):
        print(f"Error: File not found: {json_path}")
        return
    
    orchestrator = ReportOrchestrator()
    result = await orchestrator.generate_report(json_path)
    
    # Save intermediate result
    output_path = f"report_sections_{result['metadata']['task_id']}.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'sections': result['sections'],
            'metadata': result['metadata']
        }, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📁 Sections saved to: {output_path}")
    print("\nNext step: Run document_builder.py to generate DOCX")


if __name__ == "__main__":
    asyncio.run(main())

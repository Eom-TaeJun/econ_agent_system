"""
Claude Agent - Code Writing Specialist
Handles code generation, data analysis scripts, and visualization
"""
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from core.base_agent import BaseAgent, AgentRegistry
from core.message_bus import AgentRole, TaskContext, MessageType
from core.config import API_CONFIG, MODELS
import json
import re

class ClaudeAgent(BaseAgent):
    """Agent specialized in code generation using Claude API"""
    
    def __init__(self):
        super().__init__(AgentRole.CODER, "Claude-Coder")
        self.base_url = "https://api.anthropic.com/v1"
    
    def _setup_client(self):
        """Setup Anthropic API client"""
        self.api_key = API_CONFIG.anthropic_key
        if not self.api_key:
            self.logger.warning("Anthropic API key not found!")
    
    async def process(self, task: str, context: TaskContext) -> Dict[str, Any]:
        """
        Process a coding task
        
        Args:
            task: Code generation request
            context: Current task context with data/research info
            
        Returns:
            Dictionary with generated code and explanations
        """
        self.log_progress(f"Generating code for: {task[:50]}...")
        
        try:
            # Build coding prompt with context
            coding_prompt = self._build_coding_prompt(task, context)
            
            # Call Claude API
            result = await self._call_api(coding_prompt)
            
            # Extract and validate code
            code_result = self._extract_code(result)
            
            # Update context
            if code_result.get('code'):
                context.generated_code.append(code_result['code'])
            
            self.log_success(f"Code generated: {code_result.get('language', 'unknown')}")
            
            # Send results to orchestrator
            self.send_message(
                receiver=AgentRole.ORCHESTRATOR,
                content=code_result,
                msg_type=MessageType.RESULT,
                task_id=context.task_id
            )
            
            return code_result
            
        except Exception as e:
            self.log_error(f"Code generation failed: {str(e)}")
            context.errors.append(f"Coding error: {str(e)}")
            return {"error": str(e), "code": None}
    
    def _build_coding_prompt(self, task: str, context: TaskContext) -> str:
        """Build a coding-focused prompt with context"""
        
        # Summarize available data
        data_summary = ""
        if context.collected_data:
            data_summary = f"""
Available Data:
{json.dumps(list(context.collected_data.keys()), indent=2)}
Sample columns/features: {self._summarize_data(context.collected_data)}
"""
        
        # Summarize research findings
        research_summary = ""
        if context.search_results:
            variables = []
            for sr in context.search_results:
                variables.extend(sr.get('variables', []))
            research_summary = f"""
Research Findings:
- Potential variables identified: {list(set(variables))}
- Data sources found: {[sr.get('data_sources', []) for sr in context.search_results]}
"""
        
        return f"""You are an expert data scientist and economist writing Python code.

TASK: {task}

CONTEXT:
- Original Query: {context.original_query}
- Current Phase: {context.current_phase}
{data_summary}
{research_summary}

REQUIREMENTS:
1. Write clean, well-documented Python code
2. Use pandas for data manipulation
3. Use statsmodels or scikit-learn for analysis
4. Use matplotlib/seaborn/plotly for visualization
5. Include error handling
6. Add comments explaining economic intuition
7. Output should be suitable for Jupyter notebook

CODE STRUCTURE:
1. Imports
2. Data loading/preparation
3. Exploratory Data Analysis (EDA)
4. Statistical analysis (correlation, regression, etc.)
5. Visualization
6. Summary of findings

Focus on finding meaningful economic variables and relationships.
Return ONLY the code with comments, wrapped in ```python ... ```"""
    
    async def _call_api(self, prompt: str) -> Dict:
        """Call Claude API"""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": MODELS['anthropic'],
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "system": """You are an expert Python programmer specializing in:
- Economic data analysis
- Statistical modeling
- Data visualization
- Finding meaningful patterns in economic data

Write production-quality code with clear documentation."""
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    def _extract_code(self, api_response: Dict) -> Dict:
        """Extract code blocks from response"""
        try:
            content = api_response['content'][0]['text']
            
            # Extract code blocks
            code_blocks = re.findall(r'```(\w+)?\n(.*?)```', content, re.DOTALL)
            
            if code_blocks:
                language = code_blocks[0][0] or 'python'
                code = code_blocks[0][1].strip()
                
                # Extract all code if multiple blocks
                all_code = '\n\n'.join([block[1].strip() for block in code_blocks])
                
                return {
                    "code": all_code,
                    "language": language,
                    "explanation": self._extract_explanation(content, code_blocks),
                    "full_response": content,
                    "imports": self._extract_imports(all_code),
                    "functions": self._extract_functions(all_code)
                }
            else:
                # No code blocks, might be inline code
                return {
                    "code": content,
                    "language": "python",
                    "explanation": "",
                    "full_response": content,
                    "imports": [],
                    "functions": []
                }
                
        except (KeyError, IndexError) as e:
            return {
                "code": None,
                "error": str(e),
                "full_response": str(api_response)
            }
    
    def _extract_explanation(self, content: str, code_blocks: List) -> str:
        """Extract non-code explanation"""
        explanation = content
        for block in code_blocks:
            explanation = explanation.replace(f'```{block[0]}\n{block[1]}```', '')
        return explanation.strip()
    
    def _extract_imports(self, code: str) -> List[str]:
        """Extract import statements"""
        imports = re.findall(r'^(?:from\s+\S+\s+)?import\s+.+$', code, re.MULTILINE)
        return imports
    
    def _extract_functions(self, code: str) -> List[str]:
        """Extract function names"""
        functions = re.findall(r'def\s+(\w+)\s*\(', code)
        return functions
    
    def _summarize_data(self, data: Dict) -> str:
        """Summarize available data structure"""
        summary = []
        for key, value in data.items():
            if isinstance(value, dict):
                summary.append(f"{key}: {list(value.keys())[:5]}")
            elif isinstance(value, list) and len(value) > 0:
                if isinstance(value[0], dict):
                    summary.append(f"{key}: {list(value[0].keys())[:5]}")
                else:
                    summary.append(f"{key}: list[{len(value)}]")
        return "; ".join(summary[:5])
    
    async def generate_specific(self, 
                               code_type: str,
                               context: TaskContext) -> Dict:
        """Generate specific type of code"""
        type_tasks = {
            "eda": "Write exploratory data analysis code",
            "regression": "Write regression analysis code",
            "visualization": "Write data visualization code",
            "feature_engineering": "Write feature engineering code",
            "time_series": "Write time series analysis code",
            "correlation": "Write correlation analysis code"
        }
        
        task = type_tasks.get(code_type, code_type)
        return await self.process(task, context)
    
    async def refine_code(self, 
                         original_code: str, 
                         feedback: str,
                         context: TaskContext) -> Dict:
        """Refine existing code based on feedback"""
        prompt = f"""Refine this code based on the feedback:

ORIGINAL CODE:
```python
{original_code}
```

FEEDBACK:
{feedback}

Please improve the code addressing the feedback while maintaining functionality.
Return the improved code wrapped in ```python ... ```"""
        
        result = await self._call_api(prompt)
        return self._extract_code(result)


# Register agent
def create_claude_agent() -> ClaudeAgent:
    agent = ClaudeAgent()
    AgentRegistry.register(agent)
    return agent

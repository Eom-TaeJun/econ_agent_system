"""
OpenAI Orchestrator Agent - Project Supervisor
Coordinates all agents, manages workflow, and ensures quality
"""
import asyncio
import httpx
from typing import List, Dict, Any, Optional, Callable
from core.base_agent import BaseAgent, AgentRegistry
from core.message_bus import (
    AgentRole, TaskContext, MessageType, Message, MESSAGE_BUS
)
from core.config import API_CONFIG, MODELS, AGENT_CONFIG
import json
import uuid
from datetime import datetime

class OpenAIOrchestrator(BaseAgent):
    """Master orchestrator using OpenAI GPT-4"""
    
    def __init__(self):
        super().__init__(AgentRole.ORCHESTRATOR, "OpenAI-Orchestrator")
        self.base_url = "https://api.openai.com/v1"
        self.current_context: Optional[TaskContext] = None
        self.iteration_count = 0
        self.user_callback: Optional[Callable] = None
    
    def _setup_client(self):
        """Setup OpenAI API client"""
        self.api_key = API_CONFIG.openai_key
        if not self.api_key:
            self.logger.warning("OpenAI API key not found!")
    
    def set_user_callback(self, callback: Callable):
        """Set callback for user interaction"""
        self.user_callback = callback
    
    async def run_project(self, 
                         query: str,
                         auto_mode: bool = False) -> Dict[str, Any]:
        """
        Main entry point - run a complete project
        
        Args:
            query: User's project request
            auto_mode: If True, skip user checkpoints
            
        Returns:
            Complete project results
        """
        # Initialize context
        self.current_context = TaskContext(
            task_id=str(uuid.uuid4())[:8],
            original_query=query,
            current_phase="initialization"
        )
        
        self.log_progress(f"Starting project: {query[:50]}...")
        print("\n" + "="*60)
        print(f"🚀 PROJECT STARTED: {self.current_context.task_id}")
        print(f"📋 Query: {query}")
        print("="*60 + "\n")
        
        try:
            # Phase 1: Planning
            plan = await self._create_plan(query)
            
            # Phase 2: Execute plan
            results = await self._execute_plan(plan, auto_mode)
            
            # Phase 3: Synthesize results
            final_output = await self._synthesize_results(results)
            
            self.log_success("Project completed successfully!")
            
            return {
                "task_id": self.current_context.task_id,
                "query": query,
                "plan": plan,
                "results": results,
                "final_output": final_output,
                "context": self.current_context
            }
            
        except Exception as e:
            self.log_error(f"Project failed: {str(e)}")
            return {
                "task_id": self.current_context.task_id,
                "error": str(e),
                "context": self.current_context
            }
    
    async def _create_plan(self, query: str) -> Dict:
        """Create execution plan using GPT-4"""
        self.current_context.current_phase = "planning"
        self.log_progress("Creating execution plan...")
        
        prompt = f"""You are the project orchestrator for an economic analysis system.

USER REQUEST: {query}

AVAILABLE AGENTS:
1. Perplexity (Searcher): Web research, academic papers, data source discovery
2. Claude (Coder): Python code generation, data analysis, visualization
3. Gemini (Collector): Data collection, API calls, data processing

Create a detailed execution plan with the following structure:

{{
    "project_title": "...",
    "objective": "...",
    "phases": [
        {{
            "phase_number": 1,
            "name": "Research",
            "agent": "perplexity",
            "tasks": ["task1", "task2"],
            "expected_output": "..."
        }},
        {{
            "phase_number": 2,
            "name": "Data Collection",
            "agent": "gemini",
            "tasks": ["task1", "task2"],
            "expected_output": "...",
            "depends_on": [1]
        }},
        {{
            "phase_number": 3,
            "name": "Analysis & Coding",
            "agent": "claude",
            "tasks": ["task1", "task2"],
            "expected_output": "...",
            "depends_on": [1, 2]
        }}
    ],
    "success_criteria": ["criterion1", "criterion2"],
    "potential_variables": ["var1", "var2"],
    "estimated_time": "..."
}}

Focus on:
- Finding meaningful economic variables
- Data-driven analysis
- Clear, actionable steps
- Dependencies between phases"""
        
        result = await self._call_api(prompt)
        plan = self._parse_plan(result)
        
        print("\n📋 EXECUTION PLAN:")
        print("-" * 40)
        for phase in plan.get('phases', []):
            print(f"  Phase {phase.get('phase_number')}: {phase.get('name')} [{phase.get('agent')}]")
        print("-" * 40 + "\n")
        
        return plan
    
    async def _execute_plan(self, plan: Dict, auto_mode: bool) -> Dict:
        """Execute the plan phase by phase"""
        results = {}
        phases = plan.get('phases', [])
        
        for phase in phases:
            phase_num = phase.get('phase_number')
            phase_name = phase.get('name')
            agent_name = phase.get('agent', '').lower()
            tasks = phase.get('tasks', [])
            
            self.current_context.current_phase = phase_name
            self.iteration_count += 1
            
            print(f"\n🔄 PHASE {phase_num}: {phase_name}")
            print(f"   Agent: {agent_name}")
            
            # Check for user intervention
            if not auto_mode and self.iteration_count % AGENT_CONFIG.checkpoint_frequency == 0:
                should_continue = await self._checkpoint(phase)
                if not should_continue:
                    self.log_progress("User requested pause")
                    break
            
            # Execute phase
            try:
                if agent_name == 'perplexity':
                    phase_result = await self._run_searcher(tasks)
                elif agent_name == 'claude':
                    phase_result = await self._run_coder(tasks)
                elif agent_name == 'gemini':
                    phase_result = await self._run_collector(tasks)
                else:
                    phase_result = {"error": f"Unknown agent: {agent_name}"}
                
                results[f"phase_{phase_num}"] = {
                    "name": phase_name,
                    "agent": agent_name,
                    "result": phase_result
                }
                
                print(f"   ✅ Phase {phase_num} completed")
                
            except Exception as e:
                self.log_error(f"Phase {phase_num} failed: {str(e)}")
                results[f"phase_{phase_num}"] = {"error": str(e)}
        
        return results
    
    async def _run_searcher(self, tasks: List[str]) -> Dict:
        """Delegate to Perplexity agent"""
        from agents.perplexity_agent import PerplexityAgent
        
        agent = AgentRegistry.get(AgentRole.SEARCHER)
        if not agent:
            agent = PerplexityAgent()
            AgentRegistry.register(agent)
        
        all_results = []
        for task in tasks:
            result = await agent.process(task, self.current_context)
            all_results.append(result)
        
        return {"tasks_completed": len(tasks), "results": all_results}
    
    async def _run_coder(self, tasks: List[str]) -> Dict:
        """Delegate to Claude agent"""
        from agents.claude_agent import ClaudeAgent
        
        agent = AgentRegistry.get(AgentRole.CODER)
        if not agent:
            agent = ClaudeAgent()
            AgentRegistry.register(agent)
        
        all_results = []
        for task in tasks:
            result = await agent.process(task, self.current_context)
            all_results.append(result)
        
        return {"tasks_completed": len(tasks), "results": all_results}
    
    async def _run_collector(self, tasks: List[str]) -> Dict:
        """Delegate to Gemini agent"""
        from agents.gemini_agent import GeminiAgent
        
        agent = AgentRegistry.get(AgentRole.COLLECTOR)
        if not agent:
            agent = GeminiAgent()
            AgentRegistry.register(agent)
        
        all_results = []
        for task in tasks:
            result = await agent.process(task, self.current_context)
            all_results.append(result)
        
        return {"tasks_completed": len(tasks), "results": all_results}
    
    async def _checkpoint(self, current_phase: Dict) -> bool:
        """User intervention checkpoint"""
        print("\n" + "="*50)
        print("⏸️  CHECKPOINT - User Intervention Point")
        print("="*50)
        print(f"Current Phase: {current_phase.get('name')}")
        print(f"Progress: {self.current_context.to_summary()}")
        print("\nOptions:")
        print("  [c] Continue")
        print("  [m] Modify plan")
        print("  [s] Skip to next phase")
        print("  [q] Quit")
        print("="*50)
        
        if self.user_callback:
            response = await self.user_callback("checkpoint", current_phase)
        else:
            # Default: continue
            try:
                response = input("\nYour choice [c/m/s/q]: ").strip().lower()
            except:
                response = 'c'
        
        if response == 'q':
            return False
        elif response == 'm':
            # Allow user to provide modification
            modification = input("Enter modification: ")
            self.current_context.user_feedback.append(modification)
        
        return True
    
    async def _synthesize_results(self, results: Dict) -> Dict:
        """Create final synthesis of all results"""
        self.current_context.current_phase = "synthesis"
        self.log_progress("Synthesizing final results...")
        
        prompt = f"""Synthesize the following project results into a comprehensive summary:

PROJECT CONTEXT:
- Original Query: {self.current_context.original_query}
- Task ID: {self.current_context.task_id}

PHASE RESULTS:
{json.dumps(results, indent=2, default=str)[:8000]}

COLLECTED DATA SUMMARY:
{list(self.current_context.collected_data.keys())}

CODE GENERATED:
{len(self.current_context.generated_code)} code snippets

Create a synthesis with:
1. EXECUTIVE SUMMARY
   - Key findings
   - Meaningful variables identified
   - Data-driven insights

2. METHODOLOGY
   - Research approach
   - Data sources used
   - Analysis techniques

3. RESULTS
   - Main findings
   - Statistical relationships
   - Visualizations created

4. RECOMMENDATIONS
   - Further analysis suggestions
   - Data quality notes
   - Limitations

5. DELIVERABLES
   - List of generated code files
   - Datasets collected
   - Outputs produced

Format as a professional report."""
        
        result = await self._call_api(prompt)
        
        try:
            synthesis = result['choices'][0]['message']['content']
        except:
            synthesis = str(result)
        
        return {
            "synthesis": synthesis,
            "generated_at": datetime.now().isoformat(),
            "total_phases": len(results),
            "errors_count": len(self.current_context.errors)
        }
    
    async def _call_api(self, prompt: str) -> Dict:
        """Call OpenAI API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": MODELS['openai'],
            "messages": [
                {
                    "role": "system",
                    "content": """You are a master orchestrator for economic analysis projects.
Your role is to:
- Create detailed execution plans
- Coordinate multiple AI agents
- Synthesize results
- Ensure quality and completeness
- Focus on finding meaningful economic variables"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4096
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    def _parse_plan(self, api_response: Dict) -> Dict:
        """Parse API response into execution plan"""
        try:
            content = api_response['choices'][0]['message']['content']
            
            # Try to extract JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # Fallback
            return {
                "phases": [
                    {"phase_number": 1, "name": "Research", "agent": "perplexity", 
                     "tasks": ["Research the topic"]},
                    {"phase_number": 2, "name": "Data Collection", "agent": "gemini",
                     "tasks": ["Collect relevant data"]},
                    {"phase_number": 3, "name": "Analysis", "agent": "claude",
                     "tasks": ["Analyze data and create visualizations"]}
                ],
                "raw_plan": content
            }
            
        except (KeyError, IndexError) as e:
            return {"error": str(e), "raw_response": str(api_response)}
    
    async def process(self, task: str, context: TaskContext) -> Any:
        """Process a single task (required by base class)"""
        return await self.run_project(task)


# Factory function
def create_orchestrator() -> OpenAIOrchestrator:
    orchestrator = OpenAIOrchestrator()
    AgentRegistry.register(orchestrator)
    return orchestrator

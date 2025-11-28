"""
Perplexity Agent - Research & Search Specialist
Handles web research, academic paper search, and economic data discovery
"""
import asyncio
import httpx
from typing import List, Dict, Any
from core.base_agent import BaseAgent, AgentRegistry
from core.message_bus import AgentRole, TaskContext, MessageType
from core.config import API_CONFIG, MODELS

class PerplexityAgent(BaseAgent):
    """Agent specialized in research and web search using Perplexity API"""
    
    def __init__(self):
        super().__init__(AgentRole.SEARCHER, "Perplexity-Searcher")
        self.base_url = "https://api.perplexity.ai"
    
    def _setup_client(self):
        """Setup Perplexity API client"""
        self.api_key = API_CONFIG.perplexity_key
        if not self.api_key:
            self.logger.warning("Perplexity API key not found!")
    
    async def process(self, task: str, context: TaskContext) -> Dict[str, Any]:
        """
        Process a research task
        
        Args:
            task: Research query or topic
            context: Current task context
            
        Returns:
            Dictionary with search results and sources
        """
        self.log_progress(f"Starting research: {task[:50]}...")
        
        try:
            # Build research prompt focused on economics
            research_prompt = self._build_research_prompt(task, context)
            
            # Call Perplexity API
            result = await self._call_api(research_prompt)
            
            # Parse and structure results
            structured_results = self._structure_results(result, task)
            
            # Update context
            context.search_results.append(structured_results)
            
            self.log_success(f"Research completed: {len(structured_results.get('findings', []))} findings")
            
            # Send results to orchestrator
            self.send_message(
                receiver=AgentRole.ORCHESTRATOR,
                content=structured_results,
                msg_type=MessageType.RESULT,
                task_id=context.task_id
            )
            
            return structured_results
            
        except Exception as e:
            self.log_error(f"Research failed: {str(e)}")
            context.errors.append(f"Search error: {str(e)}")
            return {"error": str(e), "findings": []}
    
    def _build_research_prompt(self, task: str, context: TaskContext) -> str:
        """Build a research-focused prompt"""
        return f"""You are an economics research assistant. 

TASK: {task}

CONTEXT:
- Original Query: {context.original_query}
- Current Phase: {context.current_phase}
- Previous findings count: {len(context.search_results)}

Please provide:
1. Key findings from academic and reliable sources
2. Relevant economic indicators and data sources
3. Important variables that might be meaningful for analysis
4. Links to datasets (FRED, World Bank, IMF, etc.)
5. Recent research papers or reports on this topic

Focus on:
- Empirical evidence and data-driven insights
- Measurable economic variables
- Potential causal relationships
- Data availability and quality

Format your response with clear sections and cite sources."""
    
    async def _call_api(self, prompt: str) -> Dict:
        """Call Perplexity API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": MODELS['perplexity'],
            "messages": [
                {
                    "role": "system",
                    "content": "You are a research assistant specializing in economics and data analysis. Provide well-sourced, accurate information."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2,
            "return_citations": True,
            "return_related_questions": True
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    def _structure_results(self, api_response: Dict, original_query: str) -> Dict:
        """Structure API response into usable format"""
        try:
            content = api_response['choices'][0]['message']['content']
            citations = api_response.get('citations', [])
            related = api_response.get('related_questions', [])
            
            return {
                "query": original_query,
                "content": content,
                "citations": citations,
                "related_questions": related,
                "findings": self._extract_findings(content),
                "data_sources": self._extract_data_sources(content),
                "variables": self._extract_variables(content)
            }
        except (KeyError, IndexError) as e:
            return {
                "query": original_query,
                "content": str(api_response),
                "error": str(e),
                "findings": [],
                "data_sources": [],
                "variables": []
            }
    
    def _extract_findings(self, content: str) -> List[str]:
        """Extract key findings from content"""
        findings = []
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and (
                line.startswith(('-', '•', '*', '1', '2', '3', '4', '5')) or
                'finding' in line.lower() or
                'result' in line.lower()
            ):
                findings.append(line.lstrip('-•* 0123456789.'))
        return findings[:10]  # Top 10 findings
    
    def _extract_data_sources(self, content: str) -> List[str]:
        """Extract mentioned data sources"""
        sources = []
        keywords = ['FRED', 'World Bank', 'IMF', 'BLS', 'Census', 'OECD', 
                   'Eurostat', 'Bloomberg', 'Yahoo Finance', 'NBER', 
                   'dataset', 'database', 'API']
        
        for keyword in keywords:
            if keyword.lower() in content.lower():
                sources.append(keyword)
        return list(set(sources))
    
    def _extract_variables(self, content: str) -> List[str]:
        """Extract potential economic variables mentioned"""
        variables = []
        econ_terms = ['GDP', 'inflation', 'unemployment', 'interest rate',
                     'CPI', 'PPI', 'exchange rate', 'trade balance',
                     'money supply', 'M1', 'M2', 'federal funds rate',
                     'yield', 'spread', 'volatility', 'returns',
                     'growth rate', 'productivity', 'wage', 'employment']
        
        content_lower = content.lower()
        for term in econ_terms:
            if term.lower() in content_lower:
                variables.append(term)
        return list(set(variables))

    async def search_specific(self, 
                             query: str, 
                             search_type: str = "general") -> Dict:
        """Perform specific type of search"""
        type_prompts = {
            "academic": "Find academic papers and research on: ",
            "data": "Find datasets and data sources for: ",
            "news": "Find recent news and developments about: ",
            "methodology": "Find methodologies and approaches for analyzing: "
        }
        
        prefix = type_prompts.get(search_type, "")
        full_query = f"{prefix}{query}"
        
        return await self._call_api(full_query)


# Register agent
def create_perplexity_agent() -> PerplexityAgent:
    agent = PerplexityAgent()
    AgentRegistry.register(agent)
    return agent

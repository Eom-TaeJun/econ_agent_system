"""
Gemini Agent - Data Collection Specialist
Handles data gathering, API calls to economic databases, and data processing
"""
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from core.base_agent import BaseAgent, AgentRegistry
from core.message_bus import AgentRole, TaskContext, MessageType
from core.config import API_CONFIG, MODELS
import json
import re

class GeminiAgent(BaseAgent):
    """Agent specialized in data collection using Gemini API"""
    
    def __init__(self):
        super().__init__(AgentRole.COLLECTOR, "Gemini-Collector")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    def _setup_client(self):
        """Setup Google Gemini API client"""
        self.api_key = API_CONFIG.gemini_key
        if not self.api_key:
            self.logger.warning("Gemini API key not found!")
    
    async def process(self, task: str, context: TaskContext) -> Dict[str, Any]:
        """
        Process a data collection task
        
        Args:
            task: Data collection request
            context: Current task context
            
        Returns:
            Dictionary with collected data and metadata
        """
        self.log_progress(f"Collecting data for: {task[:50]}...")
        
        try:
            # Determine data sources and collection strategy
            collection_plan = await self._plan_collection(task, context)
            
            # Execute data collection
            collected_data = await self._execute_collection(collection_plan, context)
            
            # Update context
            context.collected_data.update(collected_data)
            
            self.log_success(f"Data collected: {len(collected_data)} datasets")
            
            # Send results to orchestrator
            self.send_message(
                receiver=AgentRole.ORCHESTRATOR,
                content={
                    "datasets": collected_data,
                    "plan": collection_plan,
                    "summary": self._summarize_collection(collected_data)
                },
                msg_type=MessageType.DATA,
                task_id=context.task_id
            )
            
            return collected_data
            
        except Exception as e:
            self.log_error(f"Data collection failed: {str(e)}")
            context.errors.append(f"Collection error: {str(e)}")
            return {"error": str(e)}
    
    async def _plan_collection(self, task: str, context: TaskContext) -> Dict:
        """Plan data collection strategy using Gemini"""
        
        # Build planning prompt
        prompt = f"""You are a data collection specialist for economic analysis.

TASK: {task}

CONTEXT:
- Original Query: {context.original_query}
- Variables identified from research: {self._get_variables(context)}
- Data sources mentioned: {self._get_sources(context)}

Please create a data collection plan:

1. DATASETS NEEDED:
   - List specific datasets required
   - For each: name, source, variables, time range

2. DATA SOURCES:
   - FRED (Federal Reserve Economic Data)
   - World Bank API
   - IMF Data
   - Yahoo Finance
   - Other relevant APIs

3. COLLECTION CODE:
   - Provide Python code to fetch each dataset
   - Use pandas_datareader, yfinance, wbdata, etc.
   - Include error handling

4. DATA PROCESSING:
   - Required transformations
   - Handling missing values
   - Frequency alignment

Return a structured JSON plan with:
{{
    "datasets": [
        {{
            "name": "...",
            "source": "...",
            "variables": [...],
            "time_range": "...",
            "fetch_code": "..."
        }}
    ],
    "processing_steps": [...],
    "estimated_rows": "..."
}}"""
        
        result = await self._call_api(prompt)
        return self._parse_plan(result)
    
    async def _call_api(self, prompt: str) -> Dict:
        """Call Gemini API"""
        url = f"{self.base_url}/models/{MODELS['gemini']}:generateContent"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 4096
            }
        }
        
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{url}?key={self.api_key}",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    def _parse_plan(self, api_response: Dict) -> Dict:
        """Parse Gemini response into collection plan"""
        try:
            content = api_response['candidates'][0]['content']['parts'][0]['text']
            
            # Try to extract JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # Fallback: parse as structured text
            return {
                "datasets": self._extract_datasets(content),
                "processing_steps": self._extract_steps(content),
                "raw_plan": content
            }
            
        except (KeyError, IndexError) as e:
            return {
                "error": str(e),
                "raw_response": str(api_response)
            }
    
    async def _execute_collection(self, plan: Dict, context: TaskContext) -> Dict:
        """Execute the data collection plan"""
        collected = {}
        
        datasets = plan.get('datasets', [])
        
        for dataset in datasets:
            dataset_name = dataset.get('name', 'unknown')
            source = dataset.get('source', '').lower()
            
            try:
                # Generate and provide collection instructions
                if 'fred' in source:
                    collected[dataset_name] = await self._get_fred_instructions(dataset)
                elif 'world bank' in source or 'wbdata' in source:
                    collected[dataset_name] = await self._get_worldbank_instructions(dataset)
                elif 'yahoo' in source or 'yfinance' in source:
                    collected[dataset_name] = await self._get_yahoo_instructions(dataset)
                else:
                    collected[dataset_name] = await self._get_generic_instructions(dataset)
                    
            except Exception as e:
                collected[dataset_name] = {"error": str(e)}
                self.log_error(f"Failed to collect {dataset_name}: {e}")
        
        return collected
    
    async def _get_fred_instructions(self, dataset: Dict) -> Dict:
        """Get FRED data collection instructions"""
        variables = dataset.get('variables', [])
        
        code = f'''# FRED Data Collection
from fredapi import Fred
import pandas as pd

# Initialize FRED API (requires FRED_API_KEY)
fred = Fred(api_key=os.environ.get('FRED_API_KEY'))

# Variables to fetch: {variables}
data = {{}}
for var in {variables}:
    try:
        data[var] = fred.get_series(var)
    except Exception as e:
        print(f"Error fetching {{var}}: {{e}}")

# Combine into DataFrame
df = pd.DataFrame(data)
df.index.name = 'date'
'''
        
        return {
            "source": "FRED",
            "variables": variables,
            "fetch_code": code,
            "requires": ["fredapi", "FRED_API_KEY"],
            "documentation": "https://fred.stlouisfed.org/docs/api/fred/"
        }
    
    async def _get_worldbank_instructions(self, dataset: Dict) -> Dict:
        """Get World Bank data collection instructions"""
        variables = dataset.get('variables', [])
        
        code = f'''# World Bank Data Collection
import wbdata
import pandas as pd

# Indicators to fetch (World Bank codes)
indicators = {variables}

# Fetch data
data = wbdata.get_dataframe(
    indicators,
    country=['USA', 'CHN', 'DEU', 'JPN', 'GBR'],  # Modify as needed
    convert_date=True
)

# Clean and reshape
df = data.reset_index()
'''
        
        return {
            "source": "World Bank",
            "variables": variables,
            "fetch_code": code,
            "requires": ["wbdata"],
            "documentation": "https://data.worldbank.org/indicator"
        }
    
    async def _get_yahoo_instructions(self, dataset: Dict) -> Dict:
        """Get Yahoo Finance data collection instructions"""
        variables = dataset.get('variables', [])
        
        code = f'''# Yahoo Finance Data Collection
import yfinance as yf
import pandas as pd

# Tickers to fetch
tickers = {variables}

# Fetch historical data
data = yf.download(
    tickers,
    start='2010-01-01',
    end=pd.Timestamp.today().strftime('%Y-%m-%d'),
    auto_adjust=True
)

# For multiple tickers, data is MultiIndex
df = data['Close'] if len(tickers) > 1 else data
'''
        
        return {
            "source": "Yahoo Finance",
            "variables": variables,
            "fetch_code": code,
            "requires": ["yfinance"],
            "documentation": "https://pypi.org/project/yfinance/"
        }
    
    async def _get_generic_instructions(self, dataset: Dict) -> Dict:
        """Get generic data collection instructions"""
        return {
            "source": dataset.get('source', 'unknown'),
            "variables": dataset.get('variables', []),
            "instructions": "Manual data collection may be required",
            "fetch_code": dataset.get('fetch_code', '# Custom collection needed')
        }
    
    def _get_variables(self, context: TaskContext) -> List[str]:
        """Extract variables from search results"""
        variables = []
        for sr in context.search_results:
            variables.extend(sr.get('variables', []))
        return list(set(variables))
    
    def _get_sources(self, context: TaskContext) -> List[str]:
        """Extract data sources from search results"""
        sources = []
        for sr in context.search_results:
            sources.extend(sr.get('data_sources', []))
        return list(set(sources))
    
    def _extract_datasets(self, content: str) -> List[Dict]:
        """Extract dataset info from text content"""
        # Simple extraction - look for numbered items or bullet points
        datasets = []
        lines = content.split('\n')
        current_dataset = {}
        
        for line in lines:
            line = line.strip()
            if 'dataset' in line.lower() or 'data source' in line.lower():
                if current_dataset:
                    datasets.append(current_dataset)
                current_dataset = {"name": line}
        
        if current_dataset:
            datasets.append(current_dataset)
            
        return datasets
    
    def _extract_steps(self, content: str) -> List[str]:
        """Extract processing steps from content"""
        steps = []
        lines = content.split('\n')
        for line in lines:
            if re.match(r'^\d+\.', line.strip()):
                steps.append(line.strip())
        return steps
    
    def _summarize_collection(self, collected: Dict) -> str:
        """Summarize collected data"""
        summary = []
        for name, data in collected.items():
            if isinstance(data, dict):
                source = data.get('source', 'unknown')
                vars_count = len(data.get('variables', []))
                summary.append(f"- {name}: {source} ({vars_count} variables)")
        return "\n".join(summary)


# Register agent
def create_gemini_agent() -> GeminiAgent:
    agent = GeminiAgent()
    AgentRegistry.register(agent)
    return agent

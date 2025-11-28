"""
Configuration module for Multi-Agent Economics Analysis System
Loads API keys from environment variables (set via WSL nano/export)
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class APIConfig:
    """API configuration container"""
    openai_key: Optional[str] = None
    anthropic_key: Optional[str] = None  # Claude
    gemini_key: Optional[str] = None
    perplexity_key: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'APIConfig':
        """Load API keys from environment variables"""
        return cls(
            openai_key=os.getenv('OPENAI_API_KEY'),
            anthropic_key=os.getenv('ANTHROPIC_API_KEY') or os.getenv('CLAUDE_API_KEY'),
            gemini_key=os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'),
            perplexity_key=os.getenv('PERPLEXITY_API_KEY')
        )
    
    def validate(self) -> dict:
        """Check which APIs are available"""
        return {
            'openai': bool(self.openai_key),
            'anthropic': bool(self.anthropic_key),
            'gemini': bool(self.gemini_key),
            'perplexity': bool(self.perplexity_key)
        }

@dataclass
class AgentConfig:
    """Agent behavior configuration"""
    max_iterations: int = 10
    checkpoint_frequency: int = 3  # Ask user every N steps
    auto_mode: bool = False  # If True, skip checkpoints
    verbose: bool = True
    log_to_file: bool = True
    output_dir: str = "outputs"
    data_dir: str = "data"

# Global configuration instance
API_CONFIG = APIConfig.from_env()
AGENT_CONFIG = AgentConfig()

# Model specifications for each provider
MODELS = {
    'openai': 'gpt-4o',  # Orchestrator
    'anthropic': 'claude-sonnet-4-20250514',  # Coder
    'gemini': 'gemini-2.0-flash',  # Data collector
    'perplexity': 'sonar-pro'  # Searcher
}

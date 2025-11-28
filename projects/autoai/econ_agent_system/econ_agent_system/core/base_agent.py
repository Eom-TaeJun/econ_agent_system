"""
Base Agent Class
Abstract base for all AI agents in the system
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
import time
from core.message_bus import (
    Message, MessageType, AgentRole, 
    MessageBus, MESSAGE_BUS, TaskContext
)
from core.config import API_CONFIG, AGENT_CONFIG

class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, role: AgentRole, name: str):
        self.role = role
        self.name = name
        self.logger = logging.getLogger(name)
        self.bus = MESSAGE_BUS
        self.is_running = False
        self._setup_client()
    
    @abstractmethod
    def _setup_client(self):
        """Initialize the API client for this agent"""
        pass
    
    @abstractmethod
    async def process(self, task: str, context: TaskContext) -> Any:
        """Process a task and return results"""
        pass
    
    def send_message(self, 
                     receiver: AgentRole, 
                     content: Any, 
                     msg_type: MessageType = MessageType.RESULT,
                     task_id: str = None,
                     metadata: Dict = None):
        """Send a message to another agent"""
        msg = Message(
            msg_type=msg_type,
            sender=self.role,
            receiver=receiver,
            content=content,
            task_id=task_id,
            metadata=metadata or {}
        )
        self.bus.send(msg)
    
    def receive_message(self, timeout: float = 30.0) -> Optional[Message]:
        """Wait for and receive a message"""
        return self.bus.receive(self.role, timeout=timeout)
    
    def request_checkpoint(self, 
                          context: TaskContext, 
                          question: str) -> Optional[str]:
        """Request user intervention/feedback"""
        self.send_message(
            receiver=AgentRole.USER,
            content={
                'question': question,
                'context_summary': context.to_summary()
            },
            msg_type=MessageType.CHECKPOINT,
            task_id=context.task_id
        )
        
        # Wait for user response
        response = self.bus.receive(AgentRole.USER, timeout=300)  # 5 min timeout
        if response:
            return response.content
        return None
    
    def log_progress(self, message: str):
        """Log progress with visual indicator"""
        self.logger.info(f"🔄 [{self.name}] {message}")
    
    def log_success(self, message: str):
        """Log success"""
        self.logger.info(f"✅ [{self.name}] {message}")
    
    def log_error(self, message: str):
        """Log error"""
        self.logger.error(f"❌ [{self.name}] {message}")


class AgentRegistry:
    """Registry to manage all active agents"""
    
    _agents: Dict[AgentRole, BaseAgent] = {}
    
    @classmethod
    def register(cls, agent: BaseAgent):
        """Register an agent"""
        cls._agents[agent.role] = agent
    
    @classmethod
    def get(cls, role: AgentRole) -> Optional[BaseAgent]:
        """Get an agent by role"""
        return cls._agents.get(role)
    
    @classmethod
    def all(cls) -> Dict[AgentRole, BaseAgent]:
        """Get all registered agents"""
        return cls._agents.copy()

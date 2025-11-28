"""
Message Bus for Inter-Agent Communication
Handles task passing, status updates, and data sharing between agents
"""
import json
import time
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Any, List, Optional, Dict
from enum import Enum
import threading
from queue import Queue
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)

class MessageType(Enum):
    TASK = "task"
    RESULT = "result"
    STATUS = "status"
    ERROR = "error"
    CHECKPOINT = "checkpoint"
    USER_INPUT = "user_input"
    DATA = "data"

class AgentRole(Enum):
    ORCHESTRATOR = "orchestrator"  # OpenAI
    SEARCHER = "searcher"          # Perplexity
    CODER = "coder"                # Claude
    COLLECTOR = "collector"        # Gemini
    USER = "user"

@dataclass
class Message:
    """Standard message format for agent communication"""
    msg_type: MessageType
    sender: AgentRole
    receiver: AgentRole
    content: Any
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    task_id: Optional[str] = None
    priority: int = 1  # 1=normal, 2=high, 3=urgent
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['msg_type'] = self.msg_type.value
        d['sender'] = self.sender.value
        d['receiver'] = self.receiver.value
        return d
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

class MessageBus:
    """Central message bus for agent communication"""
    
    def __init__(self):
        self.queues: Dict[AgentRole, Queue] = {
            role: Queue() for role in AgentRole
        }
        self.history: List[Message] = []
        self.logger = logging.getLogger("MessageBus")
        self._lock = threading.Lock()
        self._callbacks: Dict[AgentRole, List[callable]] = {
            role: [] for role in AgentRole
        }
    
    def send(self, message: Message):
        """Send a message to the target agent's queue"""
        with self._lock:
            self.queues[message.receiver].put(message)
            self.history.append(message)
            self.logger.info(
                f"[{message.sender.value}] → [{message.receiver.value}] "
                f"({message.msg_type.value})"
            )
            
            # Trigger callbacks if any
            for callback in self._callbacks.get(message.receiver, []):
                try:
                    callback(message)
                except Exception as e:
                    self.logger.error(f"Callback error: {e}")
    
    def receive(self, agent: AgentRole, timeout: float = None) -> Optional[Message]:
        """Receive a message from the agent's queue"""
        try:
            return self.queues[agent].get(timeout=timeout)
        except:
            return None
    
    def peek(self, agent: AgentRole) -> bool:
        """Check if there are messages waiting"""
        return not self.queues[agent].empty()
    
    def register_callback(self, agent: AgentRole, callback: callable):
        """Register a callback for when agent receives a message"""
        self._callbacks[agent].append(callback)
    
    def get_history(self, 
                    sender: AgentRole = None, 
                    receiver: AgentRole = None,
                    msg_type: MessageType = None) -> List[Message]:
        """Get filtered message history"""
        result = self.history
        if sender:
            result = [m for m in result if m.sender == sender]
        if receiver:
            result = [m for m in result if m.receiver == receiver]
        if msg_type:
            result = [m for m in result if m.msg_type == msg_type]
        return result
    
    def export_history(self, filepath: str):
        """Export message history to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(
                [m.to_dict() for m in self.history],
                f, indent=2, ensure_ascii=False
            )

@dataclass
class TaskContext:
    """Context passed between agents for a specific task"""
    task_id: str
    original_query: str
    current_phase: str
    search_results: List[Dict] = field(default_factory=list)
    collected_data: Dict = field(default_factory=dict)
    generated_code: List[str] = field(default_factory=list)
    analysis_results: Dict = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    user_feedback: List[str] = field(default_factory=list)
    
    def to_summary(self) -> str:
        """Generate a summary for the orchestrator"""
        return f"""
=== Task Context Summary ===
Task ID: {self.task_id}
Query: {self.original_query}
Current Phase: {self.current_phase}

Search Results: {len(self.search_results)} items
Data Collected: {list(self.collected_data.keys())}
Code Generated: {len(self.generated_code)} snippets
Errors: {len(self.errors)}
User Feedback: {len(self.user_feedback)} items
"""

# Global message bus instance
MESSAGE_BUS = MessageBus()

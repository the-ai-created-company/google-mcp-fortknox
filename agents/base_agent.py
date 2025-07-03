"""Base Agent Framework for Fort Knox Repository Agents"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

class BaseAgent:
    """Base class for all repository agents with direct access to Fort Knox documentation"""
    
    def __init__(self, agent_id: str, name: str, capabilities: List[str]):
        self.agent_id = agent_id
        self.name = name
        self.capabilities = capabilities
        self.repo_root = Path(__file__).parent.parent
        self.fort_knox_path = self.repo_root / "fort-knox-apis"
        self.mcp_tools_path = self.repo_root / "mcp-tools"
        self.shared_memory = self.repo_root / "shared-memory"
        self.agents_path = self.repo_root / "agents"
        
        # Ensure shared memory directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.shared_memory / "agent-messages",
            self.shared_memory / "task-queue",
            self.shared_memory / "knowledge-base",
            self.mcp_tools_path
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def read_fort_knox_docs(self, service: str) -> Optional[Dict[str, Any]]:
        """Direct access to Fort Knox documentation - no API calls needed!"""
        service_path = self.fort_knox_path / service
        if service_path.exists():
            docs = {}
            for file in service_path.glob("*.json"):
                with open(file, 'r', encoding='utf-8') as f:
                    docs[file.stem] = json.load(f)
            return docs
        return None
    
    def list_available_services(self) -> List[str]:
        """List all available Fort Knox API services"""
        if self.fort_knox_path.exists():
            return [d.name for d in self.fort_knox_path.iterdir() if d.is_dir()]
        return []
    
    def create_mcp_tool(self, tool_name: str, tool_code: str, category: str = "custom") -> str:
        """Create a new MCP tool directly in the repository"""
        category_path = self.mcp_tools_path / category
        category_path.mkdir(parents=True, exist_ok=True)
        
        tool_path = category_path / f"{tool_name}.ts"
        tool_path.write_text(tool_code, encoding='utf-8')
        
        # Update tool registry
        self._update_tool_registry(tool_name, category)
        
        return f"Tool {tool_name} created at {tool_path}"
    
    def _update_tool_registry(self, tool_name: str, category: str):
        """Update the master tool registry"""
        registry_path = self.mcp_tools_path / "tool_registry.json"
        registry = {}
        
        if registry_path.exists():
            with open(registry_path, 'r', encoding='utf-8') as f:
                registry = json.load(f)
        
        if category not in registry:
            registry[category] = []
        
        if tool_name not in registry[category]:
            registry[category].append(tool_name)
        
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2)
    
    def communicate(self, target_agent: str, message: Dict[str, Any]) -> bool:
        """Send message to another agent via shared memory"""
        msg_file = self.shared_memory / "agent-messages" / f"{target_agent}.json"
        messages = []
        
        if msg_file.exists():
            with open(msg_file, 'r', encoding='utf-8') as f:
                try:
                    messages = json.load(f)
                except json.JSONDecodeError:
                    messages = []
        
        messages.append({
            "from": self.agent_id,
            "to": target_agent,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "read": False
        })
        
        with open(msg_file, 'w', encoding='utf-8') as f:
            json.dump(messages, f, indent=2)
        
        return True
    
    def read_messages(self) -> List[Dict[str, Any]]:
        """Read messages sent to this agent"""
        msg_file = self.shared_memory / "agent-messages" / f"{self.agent_id}.json"
        
        if not msg_file.exists():
            return []
        
        with open(msg_file, 'r', encoding='utf-8') as f:
            try:
                messages = json.load(f)
                # Mark messages as read
                for msg in messages:
                    msg["read"] = True
                
                # Save updated messages
                with open(msg_file, 'w', encoding='utf-8') as fw:
                    json.dump(messages, fw, indent=2)
                
                return messages
            except json.JSONDecodeError:
                return []
    
    def add_task_to_queue(self, task: Dict[str, Any]) -> str:
        """Add a task to the shared task queue"""
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.agent_id}"
        task["task_id"] = task_id
        task["created_by"] = self.agent_id
        task["created_at"] = datetime.now().isoformat()
        task["status"] = "pending"
        
        queue_file = self.shared_memory / "task-queue" / "tasks.json"
        tasks = []
        
        if queue_file.exists():
            with open(queue_file, 'r', encoding='utf-8') as f:
                try:
                    tasks = json.load(f)
                except json.JSONDecodeError:
                    tasks = []
        
        tasks.append(task)
        
        with open(queue_file, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, indent=2)
        
        return task_id
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Get pending tasks from the queue"""
        queue_file = self.shared_memory / "task-queue" / "tasks.json"
        
        if not queue_file.exists():
            return []
        
        with open(queue_file, 'r', encoding='utf-8') as f:
            try:
                tasks = json.load(f)
                return [t for t in tasks if t.get("status") == "pending"]
            except json.JSONDecodeError:
                return []
    
    def update_task_status(self, task_id: str, status: str, result: Optional[Any] = None):
        """Update the status of a task"""
        queue_file = self.shared_memory / "task-queue" / "tasks.json"
        
        if not queue_file.exists():
            return False
        
        with open(queue_file, 'r', encoding='utf-8') as f:
            try:
                tasks = json.load(f)
            except json.JSONDecodeError:
                return False
        
        for task in tasks:
            if task.get("task_id") == task_id:
                task["status"] = status
                task["updated_at"] = datetime.now().isoformat()
                task["updated_by"] = self.agent_id
                if result is not None:
                    task["result"] = result
                break
        
        with open(queue_file, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, indent=2)
        
        return True
    
    def store_knowledge(self, key: str, value: Any, category: str = "general"):
        """Store knowledge in the shared knowledge base"""
        kb_path = self.shared_memory / "knowledge-base" / f"{category}.json"
        knowledge = {}
        
        if kb_path.exists():
            with open(kb_path, 'r', encoding='utf-8') as f:
                try:
                    knowledge = json.load(f)
                except json.JSONDecodeError:
                    knowledge = {}
        
        knowledge[key] = {
            "value": value,
            "stored_by": self.agent_id,
            "stored_at": datetime.now().isoformat()
        }
        
        kb_path.parent.mkdir(parents=True, exist_ok=True)
        with open(kb_path, 'w', encoding='utf-8') as f:
            json.dump(knowledge, f, indent=2)
    
    def retrieve_knowledge(self, key: str, category: str = "general") -> Optional[Any]:
        """Retrieve knowledge from the shared knowledge base"""
        kb_path = self.shared_memory / "knowledge-base" / f"{category}.json"
        
        if not kb_path.exists():
            return None
        
        with open(kb_path, 'r', encoding='utf-8') as f:
            try:
                knowledge = json.load(f)
                if key in knowledge:
                    return knowledge[key]["value"]
            except json.JSONDecodeError:
                pass
        
        return None
    
    def spawn_agent(self, agent_type: str, agent_config: Dict[str, Any]) -> str:
        """Create a new agent in the repository"""
        # Generate agent ID
        agent_number = len([d for d in self.agents_path.iterdir() if d.is_dir() and d.name.startswith("agent-")]) + 1
        agent_id = f"agent-{agent_number:02d}-{agent_type}"
        
        # Create agent directory
        agent_dir = self.agents_path / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        
        # Create agent configuration
        config = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "created_by": self.agent_id,
            "created_at": datetime.now().isoformat(),
            "config": agent_config
        }
        
        config_path = agent_dir / "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        # Create basic agent.py file
        agent_code = f'''from agents.base_agent import BaseAgent

class {agent_type.title().replace("-", "")}Agent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="{agent_id}",
            name="{agent_type.title()} Agent",
            capabilities={agent_config.get("capabilities", [])}
        )
    
    def process_message(self, message: str) -> str:
        """Process incoming messages"""
        # TODO: Implement agent-specific logic
        return f"{self.name} received: {message}"
    
    def execute_task(self, task: dict) -> dict:
        """Execute assigned tasks"""
        # TODO: Implement task execution logic
        return {{"status": "completed", "result": "Task executed successfully"}}
'''
        
        agent_file = agent_dir / "agent.py"
        agent_file.write_text(agent_code, encoding='utf-8')
        
        # Create __init__.py
        init_file = agent_dir / "__init__.py"
        init_file.write_text("", encoding='utf-8')
        
        return f"Agent {agent_id} created successfully at {agent_dir}"
    
    def process_message(self, message: str) -> str:
        """Process incoming messages - to be overridden by subclasses"""
        return f"{self.name} received: {message}"
    
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute assigned tasks - to be overridden by subclasses"""
        return {"status": "completed", "result": "Base agent task execution"}

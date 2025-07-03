"""OpenWebUI Agent Connector

This module connects Open WebUI to the repository agents, allowing:
- Chat interface to communicate with agents
- Agent discovery and routing
- Message passing between UI and agents
- Real-time agent status monitoring
"""

import sys
import json
import importlib
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentConnector:
    """Connect Open WebUI to repository agents"""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.agents_path = self.repo_root / "agents"
        self.shared_memory = self.repo_root / "shared-memory"
        
        # Add repo root to Python path
        if str(self.repo_root) not in sys.path:
            sys.path.insert(0, str(self.repo_root))
        
        self.agents = {}
        self.agent_modules = {}
        self.discover_agents()
    
    def discover_agents(self) -> Dict[str, Any]:
        """Discover all agents in the repository"""
        logger.info("Discovering agents in repository...")
        
        for agent_dir in self.agents_path.iterdir():
            if agent_dir.is_dir() and agent_dir.name.startswith("agent-"):
                agent_file = agent_dir / "agent.py"
                
                if agent_file.exists():
                    try:
                        # Import the agent module
                        module_name = f"agents.{agent_dir.name}.agent"
                        module = importlib.import_module(module_name)
                        
                        # Find the agent class (ends with "Agent")
                        agent_class = None
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if (isinstance(attr, type) and 
                                attr_name.endswith("Agent") and 
                                attr_name != "BaseAgent"):
                                agent_class = attr
                                break
                        
                        if agent_class:
                            # Initialize the agent
                            agent_instance = agent_class()
                            self.agents[agent_dir.name] = agent_instance
                            self.agent_modules[agent_dir.name] = module
                            logger.info(f"Loaded agent: {agent_dir.name} - {agent_instance.name}")
                        else:
                            logger.warning(f"No agent class found in {agent_dir.name}")
                    
                    except Exception as e:
                        logger.error(f"Failed to load agent {agent_dir.name}: {e}")
                else:
                    # Agent not implemented yet - create placeholder
                    logger.info(f"Agent {agent_dir.name} not implemented yet")
        
        return self.agents
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all available agents with their information"""
        agent_list = []
        
        for agent_id, agent in self.agents.items():
            agent_info = {
                "id": agent_id,
                "name": agent.name,
                "capabilities": agent.capabilities,
                "status": "active",
                "type": self._get_agent_type(agent_id)
            }
            agent_list.append(agent_info)
        
        # Add placeholder agents
        all_agent_dirs = [d.name for d in self.agents_path.iterdir() if d.is_dir() and d.name.startswith("agent-")]
        for agent_dir in all_agent_dirs:
            if agent_dir not in self.agents:
                agent_list.append({
                    "id": agent_dir,
                    "name": self._format_agent_name(agent_dir),
                    "capabilities": ["pending_implementation"],
                    "status": "not_implemented",
                    "type": self._get_agent_type(agent_dir)
                })
        
        return sorted(agent_list, key=lambda x: x["id"])
    
    def _get_agent_type(self, agent_id: str) -> str:
        """Extract agent type from ID"""
        parts = agent_id.split("-")
        if len(parts) >= 3:
            return "-".join(parts[2:])
        return "unknown"
    
    def _format_agent_name(self, agent_id: str) -> str:
        """Format agent name from ID"""
        agent_type = self._get_agent_type(agent_id)
        return agent_type.replace("-", " ").title() + " Agent"
    
    async def chat_with_agent(self, agent_id: str, message: str, user_id: str = "user") -> Dict[str, Any]:
        """Send a chat message to a specific agent"""
        if agent_id not in self.agents:
            return {
                "success": False,
                "error": f"Agent {agent_id} not found or not implemented",
                "available_agents": list(self.agents.keys())
            }
        
        agent = self.agents[agent_id]
        
        try:
            # Process the message
            response = agent.process_message(message)
            
            # Log the interaction
            self._log_interaction(user_id, agent_id, message, response)
            
            return {
                "success": True,
                "agent_id": agent_id,
                "agent_name": agent.name,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error chatting with agent {agent_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent_id
            }
    
    def _log_interaction(self, user_id: str, agent_id: str, message: str, response: str):
        """Log chat interactions for analysis"""
        log_file = self.shared_memory / "agent-messages" / "chat_log.json"
        
        log_entry = {
            "user_id": user_id,
            "agent_id": agent_id,
            "message": message,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        
        # Read existing logs
        logs = []
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
        
        # Add new entry
        logs.append(log_entry)
        
        # Keep only last 1000 entries
        logs = logs[-1000:]
        
        # Save logs
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
    
    async def broadcast_to_agents(self, message: str, exclude_agents: List[str] = None) -> Dict[str, Any]:
        """Broadcast a message to all agents"""
        if exclude_agents is None:
            exclude_agents = []
        
        responses = {}
        
        for agent_id, agent in self.agents.items():
            if agent_id not in exclude_agents:
                try:
                    response = agent.process_message(message)
                    responses[agent_id] = {
                        "success": True,
                        "response": response
                    }
                except Exception as e:
                    responses[agent_id] = {
                        "success": False,
                        "error": str(e)
                    }
        
        return {
            "broadcast_sent": True,
            "total_agents": len(self.agents),
            "responded": len(responses),
            "responses": responses
        }
    
    def get_agent_tasks(self, agent_id: str = None) -> List[Dict[str, Any]]:
        """Get tasks for a specific agent or all agents"""
        queue_file = self.shared_memory / "task-queue" / "tasks.json"
        
        if not queue_file.exists():
            return []
        
        try:
            with open(queue_file, 'r') as f:
                tasks = json.load(f)
            
            if agent_id:
                # Filter tasks for specific agent
                agent_tasks = []
                for task in tasks:
                    if (task.get("assigned_to") == agent_id or 
                        (not task.get("assigned_to") and task.get("status") == "pending")):
                        agent_tasks.append(task)
                return agent_tasks
            else:
                return tasks
        
        except Exception as e:
            logger.error(f"Error reading tasks: {e}")
            return []
    
    def assign_task_to_agent(self, task: Dict[str, Any], agent_id: str) -> bool:
        """Assign a task to a specific agent"""
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        
        # Add task to queue with assignment
        task["assigned_to"] = agent_id
        task["assigned_at"] = datetime.now().isoformat()
        
        task_id = agent.add_task_to_queue(task)
        
        # Notify agent
        agent.communicate(agent_id, {
            "type": "task_assigned",
            "task_id": task_id,
            "task": task
        })
        
        return True
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get detailed status of an agent"""
        if agent_id not in self.agents:
            return {
                "id": agent_id,
                "status": "not_implemented",
                "active": False
            }
        
        agent = self.agents[agent_id]
        
        # Get agent's pending tasks
        tasks = self.get_agent_tasks(agent_id)
        pending_tasks = [t for t in tasks if t.get("status") == "pending"]
        completed_tasks = [t for t in tasks if t.get("status") == "completed"]
        
        # Get recent messages
        messages = agent.read_messages()
        unread_messages = [m for m in messages if not m.get("read", True)]
        
        return {
            "id": agent_id,
            "name": agent.name,
            "status": "active",
            "active": True,
            "capabilities": agent.capabilities,
            "stats": {
                "pending_tasks": len(pending_tasks),
                "completed_tasks": len(completed_tasks),
                "unread_messages": len(unread_messages),
                "total_messages": len(messages)
            },
            "last_activity": self._get_last_activity(agent_id)
        }
    
    def _get_last_activity(self, agent_id: str) -> Optional[str]:
        """Get timestamp of agent's last activity"""
        # Check chat logs
        log_file = self.shared_memory / "agent-messages" / "chat_log.json"
        
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    logs = json.load(f)
                
                # Find last activity for this agent
                agent_logs = [l for l in logs if l.get("agent_id") == agent_id]
                if agent_logs:
                    return agent_logs[-1].get("timestamp")
            except:
                pass
        
        return None
    
    def reload_agent(self, agent_id: str) -> bool:
        """Reload an agent module (useful during development)"""
        if agent_id not in self.agent_modules:
            return False
        
        try:
            # Reload the module
            module = self.agent_modules[agent_id]
            importlib.reload(module)
            
            # Re-initialize the agent
            agent_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    attr_name.endswith("Agent") and 
                    attr_name != "BaseAgent"):
                    agent_class = attr
                    break
            
            if agent_class:
                self.agents[agent_id] = agent_class()
                logger.info(f"Reloaded agent: {agent_id}")
                return True
        
        except Exception as e:
            logger.error(f"Failed to reload agent {agent_id}: {e}")
        
        return False


# FastAPI integration for Open WebUI
try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    
    class ChatMessage(BaseModel):
        agent_id: str
        message: str
        user_id: str = "user"
    
    class TaskAssignment(BaseModel):
        task: dict
        agent_id: str
    
    # Create FastAPI app
    app = FastAPI(title="Fort Knox Agent API")
    
    # Initialize connector
    connector = AgentConnector()
    
    @app.get("/agents")
    async def list_agents():
        """List all available agents"""
        return connector.list_agents()
    
    @app.post("/agents/{agent_id}/chat")
    async def chat_with_agent(agent_id: str, message: ChatMessage):
        """Chat with a specific agent"""
        result = await connector.chat_with_agent(agent_id, message.message, message.user_id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    
    @app.post("/agents/broadcast")
    async def broadcast_message(message: ChatMessage):
        """Broadcast message to all agents"""
        return await connector.broadcast_to_agents(message.message)
    
    @app.get("/agents/{agent_id}/status")
    async def get_agent_status(agent_id: str):
        """Get agent status"""
        return connector.get_agent_status(agent_id)
    
    @app.get("/agents/{agent_id}/tasks")
    async def get_agent_tasks(agent_id: str):
        """Get tasks for an agent"""
        return connector.get_agent_tasks(agent_id)
    
    @app.post("/agents/{agent_id}/reload")
    async def reload_agent(agent_id: str):
        """Reload an agent module"""
        if connector.reload_agent(agent_id):
            return {"success": True, "message": f"Agent {agent_id} reloaded"}
        raise HTTPException(status_code=500, detail="Failed to reload agent")

except ImportError:
    logger.warning("FastAPI not installed. API endpoints not available.")


# CLI Interface for testing
if __name__ == "__main__":
    connector = AgentConnector()
    
    print("\n🤖 Fort Knox Agent Connector")
    print("=" * 50)
    
    # List agents
    agents = connector.list_agents()
    print(f"\nFound {len(agents)} agents:")
    for agent in agents:
        status = "✅" if agent["status"] == "active" else "⏳"
        print(f"{status} {agent['id']}: {agent['name']}")
        print(f"   Capabilities: {', '.join(agent['capabilities'])}")
    
    # Test chat with active agents
    print("\n\nTesting agent communication...")
    for agent_id in connector.agents:
        response = asyncio.run(connector.chat_with_agent(
            agent_id, 
            "Hello! What can you do?"
        ))
        if response["success"]:
            print(f"\n{response['agent_name']}: {response['response'][:100]}...")

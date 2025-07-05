"""Enhanced Base Agent Framework with Google Gemini Integration"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio
import aiohttp
from abc import ABC, abstractmethod

class GeminiConfig:
    """Configuration for Google Gemini API"""
    API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyCULQJzJVi9VuMQM6-YaqKAzbooLyG8WD4")
    MODEL = "gemini-2.0-flash-exp"  # Latest Gemini 2.0 Flash experimental
    API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    
    # Model capabilities
    MAX_TOKENS = 1_048_576  # 1M context window
    MAX_OUTPUT_TOKENS = 8192
    TEMPERATURE = 0.7
    TOP_P = 0.95
    TOP_K = 40

class EnhancedBaseAgent(ABC):
    """Enhanced base class with Gemini AI capabilities"""
    
    def __init__(self, agent_id: str, name: str, capabilities: List[str]):
        self.agent_id = agent_id
        self.name = name
        self.capabilities = capabilities
        self.repo_root = Path(__file__).parent.parent
        self.fort_knox_path = self.repo_root / "fort-knox-apis"
        self.mcp_tools_path = self.repo_root / "mcp-tools"
        self.shared_memory = self.repo_root / "shared-memory"
        self.agents_path = self.repo_root / "agents"
        
        # Gemini configuration
        self.gemini_config = GeminiConfig()
        self.session = None
        
        # Agent memory and context
        self.conversation_history = []
        self.tool_execution_history = []
        self.knowledge_cache = {}
        
        # Ensure shared memory directories exist
        self._ensure_directories()
        
        # Load agent-specific configuration
        self._load_agent_config()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.shared_memory / "agent-messages",
            self.shared_memory / "task-queue",
            self.shared_memory / "knowledge-base",
            self.shared_memory / "agent-memory",
            self.mcp_tools_path / "generated",
            self.mcp_tools_path / "templates"
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_agent_config(self):
        """Load agent-specific configuration"""
        config_path = self.agents_path / self.agent_id / "config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "agent_id": self.agent_id,
                "name": self.name,
                "capabilities": self.capabilities,
                "gemini_settings": {
                    "temperature": self.gemini_config.TEMPERATURE,
                    "max_output_tokens": self.gemini_config.MAX_OUTPUT_TOKENS,
                    "top_p": self.gemini_config.TOP_P,
                    "top_k": self.gemini_config.TOP_K
                }
            }
            self._save_agent_config()
    
    def _save_agent_config(self):
        """Save agent configuration"""
        config_path = self.agents_path / self.agent_id / "config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def think_with_gemini(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Use Gemini to process complex reasoning tasks"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # Prepare the context
        system_prompt = self._build_system_prompt(context)
        
        # Build the request
        url = f"{self.gemini_config.API_BASE_URL}/models/{self.gemini_config.MODEL}:generateContent"
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.gemini_config.API_KEY
        }
        
        # Prepare the message with context
        messages = []
        
        # Add system context
        messages.append({
            "role": "user",
            "parts": [{"text": system_prompt}]
        })
        
        # Add conversation history (last 10 messages)
        for msg in self.conversation_history[-10:]:
            messages.append(msg)
        
        # Add current prompt
        messages.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })
        
        payload = {
            "contents": messages,
            "generationConfig": {
                "temperature": self.config["gemini_settings"]["temperature"],
                "topK": self.config["gemini_settings"]["top_k"],
                "topP": self.config["gemini_settings"]["top_p"],
                "maxOutputTokens": self.config["gemini_settings"]["max_output_tokens"],
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
        }
        
        try:
            async with self.session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract the response
                    if "candidates" in data and data["candidates"]:
                        content = data["candidates"][0]["content"]["parts"][0]["text"]
                        
                        # Store in conversation history
                        self.conversation_history.append({
                            "role": "model",
                            "parts": [{"text": content}]
                        })
                        
                        # Save to agent memory
                        self._save_to_memory("conversation", {
                            "timestamp": datetime.now().isoformat(),
                            "prompt": prompt,
                            "response": content
                        })
                        
                        return content
                    else:
                        return "No response generated"
                else:
                    error_data = await response.text()
                    return f"Error: {response.status} - {error_data}"
                    
        except Exception as e:
            return f"Error communicating with Gemini: {str(e)}"
    
    def _build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Build the system prompt with agent context"""
        prompt = f"""You are {self.name}, an autonomous AI agent with the following capabilities:
{json.dumps(self.capabilities, indent=2)}

You are part of the Fort Knox AI Agent Ecosystem, a self-modifying system where agents can:
1. Create new MCP tools dynamically
2. Spawn other specialized agents
3. Access 400+ Google Cloud API documentation locally
4. Modify your own code and improve yourself
5. Communicate with other agents through shared memory

Your current working directory is: {self.repo_root}
Available Fort Knox APIs: {', '.join(self.list_available_services())}

Context for this task:
"""
        
        if context:
            prompt += f"\n{json.dumps(context, indent=2)}"
        
        # Add recent tool executions
        if self.tool_execution_history:
            prompt += f"\n\nRecent tool executions:\n"
            for execution in self.tool_execution_history[-5:]:
                prompt += f"- {execution['tool']}: {execution['result']}\n"
        
        return prompt
    
    def _save_to_memory(self, memory_type: str, data: Any):
        """Save data to agent's persistent memory"""
        memory_path = self.shared_memory / "agent-memory" / self.agent_id / f"{memory_type}.json"
        memory_path.parent.mkdir(parents=True, exist_ok=True)
        
        memory = []
        if memory_path.exists():
            with open(memory_path, 'r', encoding='utf-8') as f:
                try:
                    memory = json.load(f)
                except json.JSONDecodeError:
                    memory = []
        
        memory.append(data)
        
        # Keep only last 100 entries
        memory = memory[-100:]
        
        with open(memory_path, 'w', encoding='utf-8') as f:
            json.dump(memory, f, indent=2)
    
    async def analyze_google_cloud_api(self, service: str) -> Dict[str, Any]:
        """Use Gemini to analyze a Google Cloud API and suggest MCP tools"""
        docs = self.read_fort_knox_docs(service)
        if not docs:
            return {"error": f"No documentation found for {service}"}
        
        prompt = f"""Analyze this Google Cloud {service} API documentation and suggest 5 useful MCP tools we should create.

Documentation:
{json.dumps(docs, indent=2)[:10000]}  # Limit to 10k chars for this example

For each tool, provide:
1. Tool name (snake_case)
2. Description
3. Key parameters
4. Example use case
5. TypeScript implementation sketch

Format your response as JSON.
"""
        
        response = await self.think_with_gemini(prompt, {"task": "api_analysis", "service": service})
        
        try:
            # Parse the JSON response
            suggestions = json.loads(response)
            return suggestions
        except json.JSONDecodeError:
            return {"raw_response": response}
    
    async def generate_mcp_tool(self, tool_spec: Dict[str, Any]) -> str:
        """Use Gemini to generate a complete MCP tool implementation"""
        prompt = f"""Generate a complete TypeScript MCP tool implementation based on this specification:

Tool Name: {tool_spec.get('name')}
Description: {tool_spec.get('description')}
Parameters: {json.dumps(tool_spec.get('parameters', {}), indent=2)}
Category: {tool_spec.get('category', 'custom')}

Requirements:
1. Follow the MCP SDK patterns
2. Include proper error handling
3. Add input validation using zod
4. Include comprehensive JSDoc comments
5. Make it production-ready

Generate the complete TypeScript code.
"""
        
        code = await self.think_with_gemini(prompt, {"task": "code_generation", "tool_spec": tool_spec})
        
        # Save the generated tool
        tool_name = tool_spec.get('name', 'unnamed_tool')
        tool_path = self.mcp_tools_path / "generated" / f"{tool_name}.ts"
        
        tool_path.write_text(code, encoding='utf-8')
        
        # Record the tool generation
        self.tool_execution_history.append({
            "tool": "generate_mcp_tool",
            "result": f"Generated {tool_name} at {tool_path}",
            "timestamp": datetime.now().isoformat()
        })
        
        return f"Tool {tool_name} generated successfully at {tool_path}"
    
    async def self_improve(self) -> str:
        """Use Gemini to analyze and improve the agent's own code"""
        # Read the agent's own code
        agent_file = self.agents_path / self.agent_id / "agent.py"
        if not agent_file.exists():
            return "Agent code file not found"
        
        current_code = agent_file.read_text(encoding='utf-8')
        
        prompt = f"""Analyze my current code and suggest improvements:

Current Code:
```python
{current_code}
```

Current Capabilities: {self.capabilities}
Recent Tasks: {json.dumps(self.tool_execution_history[-5:], indent=2)}

Suggest improvements for:
1. Better error handling
2. More efficient algorithms
3. New capabilities I should add
4. Code organization
5. Performance optimizations

Provide the improved code and explain the changes.
"""
        
        response = await self.think_with_gemini(prompt, {"task": "self_improvement"})
        
        # Save the suggestions
        suggestions_path = self.agents_path / self.agent_id / "improvement_suggestions.md"
        suggestions_path.write_text(f"# Improvement Suggestions\n\nGenerated: {datetime.now()}\n\n{response}", encoding='utf-8')
        
        return f"Self-improvement analysis complete. Suggestions saved to {suggestions_path}"
    
    # Original methods from base_agent.py (enhanced versions)
    
    def read_fort_knox_docs(self, service: str) -> Optional[Dict[str, Any]]:
        """Direct access to Fort Knox documentation - no API calls needed!"""
        service_path = self.fort_knox_path / service
        if service_path.exists():
            docs = {}
            for file in service_path.glob("*.json"):
                with open(file, 'r', encoding='utf-8') as f:
                    docs[file.stem] = json.load(f)
            return docs
        
        # Also check in extracted-data
        extracted_path = self.repo_root / "extracted-data" / service
        if extracted_path.exists():
            docs = {}
            for file in extracted_path.glob("*.json"):
                with open(file, 'r', encoding='utf-8') as f:
                    docs[file.stem] = json.load(f)
            return docs
        
        return None
    
    def list_available_services(self) -> List[str]:
        """List all available Fort Knox API services"""
        services = set()
        
        # Check fort-knox-apis
        if self.fort_knox_path.exists():
            services.update([d.name for d in self.fort_knox_path.iterdir() if d.is_dir()])
        
        # Check extracted-data
        extracted_path = self.repo_root / "extracted-data"
        if extracted_path.exists():
            services.update([d.name for d in extracted_path.iterdir() if d.is_dir()])
        
        return sorted(list(services))
    
    def create_mcp_tool(self, tool_name: str, tool_code: str, category: str = "custom") -> str:
        """Create a new MCP tool directly in the repository"""
        category_path = self.mcp_tools_path / category
        category_path.mkdir(parents=True, exist_ok=True)
        
        tool_path = category_path / f"{tool_name}.ts"
        tool_path.write_text(tool_code, encoding='utf-8')
        
        # Update tool registry
        self._update_tool_registry(tool_name, category)
        
        # Record the creation
        self.tool_execution_history.append({
            "tool": "create_mcp_tool",
            "result": f"Created {tool_name}",
            "timestamp": datetime.now().isoformat()
        })
        
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
            registry["total_tools"] = sum(len(tools) for tools in registry.values() if isinstance(tools, list))
            registry["last_updated"] = datetime.now().isoformat()
        
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2)
    
    # Abstract methods that must be implemented by subclasses
    @abstractmethod
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def handle_message(self, message: Dict[str, Any]) -> str:
        """Handle incoming messages - must be implemented by subclasses"""
        pass


# Backward compatibility
BaseAgent = EnhancedBaseAgent

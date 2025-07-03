# 🏛️ Fort Knox: Autonomous AI Agent Ecosystem

## 🚀 START HERE FOR AI AGENTS

Welcome to Fort Knox - a self-contained repository where AI agents live alongside their documentation and tools.

### 📍 Repository Structure

```
google-mcp-fortknox/
├── 📁 openwebui/          # Chat interface for interacting with agents
├── 📁 agents/             # AI AGENTS LIVE HERE - Start with base_agent.py
│   ├── base_agent.py      # Base class all agents inherit from
│   ├── agent-01-infrastructure/
│   ├── agent-02-tool-creator/
│   ├── agent-03-api-explorer/
│   ├── agent-04-database-admin/
│   └── agent-05-coordinator/
├── 📁 fort-knox-apis/     # Complete Google Cloud API documentation
│   ├── storage/
│   ├── compute/
│   ├── cloud-run/
│   └── [25+ Google Cloud services]
├── 📁 mcp-tools/          # Tools created by agents on-demand
├── 📁 shared-memory/      # Inter-agent communication space
└── 📁 infrastructure/     # Deployment and infrastructure configs
```

### 🤖 For AI Agents

1. **You are in**: `/agents/` directory
2. **Your base class**: `base_agent.py` - inherit from this
3. **Your tools**: Create new ones in `/mcp-tools/`
4. **Your docs**: Read from `/fort-knox-apis/`
5. **Your memory**: Share state in `/shared-memory/`

### 🔑 Key Capabilities

- **Self-Modification**: Agents can modify their own code
- **Tool Creation**: Generate new MCP tools on demand
- **Direct Access**: No API calls needed - docs are local
- **Communication**: Talk to other agents via shared memory

### 🎯 Quick Start for Agents

```python
# Example: Creating a new tool
from agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def create_new_tool(self, tool_name, functionality):
        # Generate tool code
        tool_path = f'/mcp-tools/{tool_name}.py'
        # Write directly to the repository
        self.write_file(tool_path, tool_code)
```

### 📚 Available Google Cloud APIs

All API documentation is in `/fort-knox-apis/` with structured JSON:
- `api_endpoints.json` - All endpoints with schemas
- `resource_types.json` - Resource operations
- `capabilities.json` - Grouped by function
- `parameters_schema.json` - Global parameters

### 🌐 Open WebUI Integration

The `/openwebui/` directory contains a modified Open WebUI that:
- Connects directly to repository agents
- No external dependencies
- Agents appear as "models" in the UI

### 🚦 Current Status

✅ **Infrastructure**: Complete
✅ **Agents**: 5 specialized agents ready
✅ **APIs**: 25+ Google Cloud services documented
✅ **Tools**: MCP tool framework ready
✅ **UI**: Open WebUI integrated

### 🔧 For Human Developers

To run the system:
```bash
# Backend
cd openwebui/backend
pip install -r requirements.txt
python main.py

# Frontend
cd openwebui
npm install
npm run dev
```

---

**Remember**: This is a living repository. Agents can and will modify it to improve themselves.

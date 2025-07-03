# OpenWebUI Integration

This directory will contain the modified Open WebUI that:
- Connects directly to repository agents
- Removes external tool dependencies  
- Provides chat interface to agents
- Allows agents to modify their own code

## Current Status

✅ **Agent Connector Ready**: The `agent_connector.py` module is complete and provides:
- Automatic agent discovery
- Chat routing to agents
- Task management
- FastAPI endpoints for integration
- Real-time agent status monitoring

## Agent Connection Architecture

```
OpenWebUI Frontend
      ↓
agent_connector.py (FastAPI)
      ↓
Repository Agents (in /agents)
      ↓
Fort Knox Docs + MCP Tools
```

## Setup Instructions

### 1. Install Open WebUI

```bash
# Clone Open WebUI into this directory
git clone https://github.com/open-webui/open-webui.git temp-openwebui
cp -r temp-openwebui/* .
rm -rf temp-openwebui
```

### 2. Install Dependencies

```bash
pip install fastapi uvicorn pydantic
```

### 3. Run Agent Connector API

```bash
cd openwebui
uvicorn agent_connector:app --reload --port 8001
```

### 4. Configure Open WebUI

Modify Open WebUI's backend to use our agent connector instead of its built-in tools:

```python
# In Open WebUI's tool handler
import requests

def chat_with_agent(agent_id: str, message: str):
    response = requests.post(
        f"http://localhost:8001/agents/{agent_id}/chat",
        json={"agent_id": agent_id, "message": message}
    )
    return response.json()
```

## API Endpoints

The agent connector provides these endpoints:

- `GET /agents` - List all available agents
- `POST /agents/{agent_id}/chat` - Chat with specific agent
- `POST /agents/broadcast` - Broadcast to all agents
- `GET /agents/{agent_id}/status` - Get agent status
- `GET /agents/{agent_id}/tasks` - Get agent tasks
- `POST /agents/{agent_id}/reload` - Reload agent module

## Testing the Connector

You can test the agent connector directly:

```bash
python agent_connector.py
```

This will:
1. Discover all agents in the repository
2. List their capabilities
3. Test basic communication

## Integration Points

### For Open WebUI Frontend

Replace the tools/functions dropdown with an agents dropdown that:
1. Calls `GET /agents` to list available agents
2. Routes messages to selected agent via `POST /agents/{agent_id}/chat`
3. Shows agent status with `GET /agents/{agent_id}/status`

### For Agent Development

Agents can be developed independently and will be automatically discovered:
1. Create new directory: `/agents/agent-XX-name/`
2. Add `agent.py` implementing the agent class
3. Restart the connector to discover the new agent

## Next Steps

1. [ ] Download and integrate Open WebUI source
2. [ ] Modify Open WebUI to use agent connector
3. [ ] Remove Open WebUI's built-in tool system
4. [ ] Add agent selection UI
5. [ ] Implement real-time status updates
6. [ ] Add agent management interface

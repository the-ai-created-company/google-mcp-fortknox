#!/bin/bash
# Download and integrate Open WebUI into the repository

echo "🌐 Downloading Open WebUI..."
echo "================================"

# Create temporary directory
TEMP_DIR="temp_openwebui_download"
mkdir -p $TEMP_DIR

# Clone Open WebUI repository
echo "📥 Cloning Open WebUI repository..."
cd $TEMP_DIR
git clone --depth 1 https://github.com/open-webui/open-webui.git

# Check if clone was successful
if [ ! -d "open-webui" ]; then
    echo "❌ Failed to clone Open WebUI"
    exit 1
fi

echo "✅ Open WebUI cloned successfully"

# Move back to root directory
cd ..

# Clear existing openwebui directory (keeping our custom files)
echo "🔄 Preparing openwebui directory..."
mv openwebui/agent_connector.py temp_agent_connector.py 2>/dev/null || true
mv openwebui/README.md temp_readme.md 2>/dev/null || true

# Copy Open WebUI source
echo "📦 Copying Open WebUI source files..."
cp -r $TEMP_DIR/open-webui/* openwebui/ || {
    echo "❌ Failed to copy Open WebUI files"
    exit 1
}

# Restore our custom files
echo "🔧 Restoring custom integration files..."
mv temp_agent_connector.py openwebui/agent_connector.py 2>/dev/null || true

# Create our custom README that includes both instructions
cat > openwebui/README.md << 'EOF'
# Open WebUI - Fort Knox Agent Interface

This directory contains the Open WebUI modified to work as a chat interface for Fort Knox agents.

## Original Open WebUI

The base Open WebUI code is from: https://github.com/open-webui/open-webui

## Fort Knox Modifications

### 1. Agent Integration
- `agent_connector.py` provides the bridge between Open WebUI and repository agents
- Agents are discovered automatically from `/agents` directory
- Direct communication without external APIs

### 2. Removed Components
- External tool system (replaced with direct agent access)
- Remote model connections (agents handle all intelligence)

### 3. Added Components
- Agent discovery system
- Direct repository access
- Task queue integration
- Shared memory access

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker (optional)

### Local Development Setup

1. **Backend Setup**
   ```bash
   cd openwebui/backend
   pip install -r requirements.txt
   
   # Add our agent connector to Python path
   export PYTHONPATH=$PYTHONPATH:../
   
   # Run with agent integration
   python main.py --agents
   ```

2. **Frontend Setup**
   ```bash
   cd openwebui
   npm install
   npm run dev
   ```

3. **Environment Configuration**
   Create `.env` file:
   ```
   # Fort Knox Configuration
   ENABLE_FORT_KNOX_AGENTS=true
   AGENT_DIRECTORY=/agents
   FORT_KNOX_API_PATH=/fort-knox-apis
   MCP_TOOLS_PATH=/mcp-tools
   
   # Disable external connections
   ENABLE_OLLAMA=false
   ENABLE_OPENAI_API=false
   ```

## Agent Communication

The Open WebUI communicates with agents through the FastAPI endpoints in `agent_connector.py`:

- `GET /agents` - List available agents
- `POST /chat` - Send message to agent
- `GET /tasks` - View task queue
- `POST /broadcast` - Message all agents

## Development Notes

1. Agents have direct file system access to Fort Knox documentation
2. No external API calls needed - everything runs locally
3. Agents can modify their own code and create new tools
4. Shared memory enables inter-agent communication

## Docker Deployment

```bash
# Build Fort Knox Open WebUI image
docker build -t fort-knox-openwebui .

# Run with volume mounts for agent access
docker run -d \
  -p 8080:8080 \
  -v $(pwd)/agents:/agents \
  -v $(pwd)/fort-knox-apis:/fort-knox-apis \
  -v $(pwd)/mcp-tools:/mcp-tools \
  -v $(pwd)/shared-memory:/shared-memory \
  fort-knox-openwebui
```
EOF

# Clean up temporary directory
echo "🧹 Cleaning up..."
rm -rf $TEMP_DIR

echo "✅ Open WebUI downloaded and integrated!"
echo ""
echo "📋 Next steps:"
echo "1. Run ./migrate_repository.sh to complete repository reorganization"
echo "2. Follow setup instructions in openwebui/README.md"
echo "3. Start Open WebUI with agent integration"

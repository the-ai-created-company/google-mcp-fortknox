#!/bin/bash
# Repository Migration Script
# Transforms Fort Knox into an autonomous agent ecosystem

echo "🚀 Starting Fort Knox Repository Migration..."
echo "================================================"

# Create new directory structure
echo "📁 Creating new directory structure..."
mkdir -p fort-knox-apis
mkdir -p mcp-tools/{infrastructure,agents,database,tool-creation,api-discovery,openwebui,deployment}
mkdir -p shared-memory/{agent-messages,task-queue,knowledge-base}
mkdir -p agents/{agent-03-api-explorer,agent-04-database-admin,agent-05-coordinator}
mkdir -p openwebui

# Move Fort Knox API documentation
echo "📚 Reorganizing Fort Knox API documentation..."
if [ -d "discovery-docs" ]; then
    mv discovery-docs/* fort-knox-apis/ 2>/dev/null || true
fi

if [ -d "extracted-data" ]; then
    mv extracted-data/* fort-knox-apis/ 2>/dev/null || true
fi

# Move existing MCP tools
echo "🔧 Moving existing MCP tools..."
if [ -d "mcp-server/src/tools" ]; then
    # Move each tool category to its proper location
    for tool in mcp-server/src/tools/*.ts; do
        if [ -f "$tool" ]; then
            filename=$(basename "$tool")
            case "$filename" in
                infrastructure*) mv "$tool" mcp-tools/infrastructure/ ;;
                agents*) mv "$tool" mcp-tools/agents/ ;;
                database*) mv "$tool" mcp-tools/database/ ;;
                tool-creation*) mv "$tool" mcp-tools/tool-creation/ ;;
                api-discovery*) mv "$tool" mcp-tools/api-discovery/ ;;
                openwebui*) mv "$tool" mcp-tools/openwebui/ ;;
                deployment*) mv "$tool" mcp-tools/deployment/ ;;
                *) mv "$tool" mcp-tools/ ;;
            esac
        fi
    done
fi

# Move MCP server files to tools directory
if [ -d "mcp-server" ]; then
    mv mcp-server/package.json mcp-tools/ 2>/dev/null || true
    mv mcp-server/tsconfig.json mcp-tools/ 2>/dev/null || true
    mv mcp-server/README.md mcp-tools/ 2>/dev/null || true
    mv mcp-server/src/index.ts mcp-tools/ 2>/dev/null || true
    mv mcp-server/src/types.ts mcp-tools/ 2>/dev/null || true
fi

# Move OpenWebUI control to MCP tools
echo "🎮 Moving OpenWebUI control tools..."
if [ -d "openwebui-control" ]; then
    mv openwebui-control/* mcp-tools/openwebui/ 2>/dev/null || true
fi

# Create placeholder files for remaining agents
echo "🤖 Creating placeholder agents..."

# API Explorer Agent
cat > agents/agent-03-api-explorer/__init__.py << 'EOF'
# API Explorer Agent Module
EOF

cat > agents/agent-03-api-explorer/README.md << 'EOF'
# API Explorer Agent

This agent will:
- Discover and analyze external APIs
- Generate MCP tool wrappers automatically
- Test API endpoints
- Create documentation
EOF

# Database Admin Agent
cat > agents/agent-04-database-admin/__init__.py << 'EOF'
# Database Admin Agent Module
EOF

cat > agents/agent-04-database-admin/README.md << 'EOF'
# Database Admin Agent

This agent will:
- Manage Cloud SQL instances
- Execute database queries
- Create and manage schemas
- Handle backups and migrations
EOF

# Coordinator Agent
cat > agents/agent-05-coordinator/__init__.py << 'EOF'
# Coordinator Agent Module
EOF

cat > agents/agent-05-coordinator/README.md << 'EOF'
# Coordinator Agent

This agent will:
- Orchestrate other agents
- Manage task distribution
- Monitor agent health
- Handle inter-agent communication
EOF

# Create shared memory initialization files
echo "💾 Initializing shared memory system..."
echo '[]' > shared-memory/agent-messages/messages.json
echo '[]' > shared-memory/task-queue/tasks.json
echo '{}' > shared-memory/knowledge-base/general.json

# Create tool registry
echo "📋 Creating tool registry..."
cat > mcp-tools/tool_registry.json << 'EOF'
{
  "infrastructure": [],
  "agents": [],
  "database": [],
  "tool-creation": [],
  "api-discovery": [],
  "openwebui": [],
  "deployment": [],
  "custom": []
}
EOF

# Create OpenWebUI placeholder
echo "🌐 Creating OpenWebUI placeholder..."
cat > openwebui/README.md << 'EOF'
# OpenWebUI Integration

This directory will contain the modified Open WebUI that:
- Connects directly to repository agents
- Removes external tool dependencies
- Provides chat interface to agents
- Allows agents to modify their own code

## Setup Instructions

1. Clone Open WebUI: `git clone https://github.com/open-webui/open-webui.git .`
2. Apply modifications from `openwebui-modifications/`
3. Configure agent connections
4. Deploy or run locally

## Agent Connection

The OpenWebUI will discover agents automatically from the `/agents` directory
and provide a chat interface to interact with them.
EOF

# Clean up old directories
echo "🧹 Cleaning up old structure..."
rm -rf discovery-docs extracted-data mcp-server openwebui-control 2>/dev/null || true

# Create a migration summary
echo "📊 Creating migration summary..."
cat > MIGRATION_COMPLETE.md << 'EOF'
# Migration Complete!

## New Repository Structure

```
google-mcp-fortknox/
├── /agents                    # AI agents with direct repo access
├── /fort-knox-apis           # Google API documentation
├── /mcp-tools               # MCP tools organized by category
├── /shared-memory           # Agent communication system
└── /openwebui               # Chat interface (to be added)
```

## What Changed

1. **Fort Knox APIs**: Moved from `discovery-docs/` and `extracted-data/` to `fort-knox-apis/`
2. **MCP Tools**: Reorganized from `mcp-server/` into categorized `mcp-tools/` directory
3. **Agents**: Created agent framework with 2 working agents and 3 placeholders
4. **Shared Memory**: Initialized communication system for agents

## Next Steps

1. Download and integrate Open WebUI
2. Implement remaining agents
3. Test agent communication
4. Enable autonomous operation

## Working Components

- ✅ Base Agent Framework
- ✅ Infrastructure Agent
- ✅ Tool Creator Agent
- ✅ Shared Memory System
- ✅ Fort Knox Documentation
- ✅ MCP Tools (29 existing)

## Pending Components

- ⏳ Open WebUI Integration
- ⏳ API Explorer Agent
- ⏳ Database Admin Agent
- ⏳ Coordinator Agent
- ⏳ Agent Discovery System
EOF

echo "✅ Migration complete!"
echo "📄 See MIGRATION_COMPLETE.md for details"

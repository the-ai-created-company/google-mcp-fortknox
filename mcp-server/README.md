# Google Cloud MCP Server for InstaBids AI Hub

This is the comprehensive MCP (Model Context Protocol) server that provides Google Cloud tools for autonomous AI agents to manage infrastructure and build themselves.

## Architecture

```
mcp-server/
├── src/
│   ├── tools/           # Individual MCP tools
│   ├── server.ts        # Main MCP server
│   ├── types.ts         # TypeScript types
│   └── config.ts        # Configuration
├── dist/                # Compiled output
├── package.json         # Dependencies
└── tsconfig.json        # TypeScript config
```

## Core Features

1. **Infrastructure Management** - Create and manage Google Cloud resources
2. **Agent Spawning** - Create new autonomous agents
3. **Tool Creation** - Dynamically create new MCP tools
4. **API Discovery** - Reverse engineer APIs and create wrappers
5. **Database Management** - Create and manage databases
6. **Service Deployment** - Deploy services to Cloud Run

## Installation

```bash
npm install
npm run build
```

## Usage

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "google-cloud-instabids": {
      "command": "node",
      "args": ["/path/to/mcp-server/dist/index.js"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/service-account.json",
        "GOOGLE_CLOUD_PROJECT": "instabids-ai-hub"
      }
    }
  }
}
```

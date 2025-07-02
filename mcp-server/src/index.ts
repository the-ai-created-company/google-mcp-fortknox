import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
import winston from 'winston';

// Import all tools
import { infrastructureTools } from './tools/infrastructure.js';
import { agentTools } from './tools/agents.js';
import { databaseTools } from './tools/database.js';
import { deploymentTools } from './tools/deployment.js';
import { monitoringTools } from './tools/monitoring.js';
import { storageTools } from './tools/storage.js';
import { networkingTools } from './tools/networking.js';
import { securityTools } from './tools/security.js';
import { billingTools } from './tools/billing.js';
import { toolCreationTools } from './tools/tool-creation.js';
import { apiDiscoveryTools } from './tools/api-discovery.js';
import { openwebuiTools } from './tools/openwebui.js';
import { workflowTools } from './tools/workflows.js';
import { integrationTools } from './tools/integrations.js';

// Configure logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'mcp-server.log' })
  ]
});

// Combine all tools
const allTools = [
  ...infrastructureTools,
  ...agentTools,
  ...databaseTools,
  ...deploymentTools,
  ...monitoringTools,
  ...storageTools,
  ...networkingTools,
  ...securityTools,
  ...billingTools,
  ...toolCreationTools,
  ...apiDiscoveryTools,
  ...openwebuiTools,
  ...workflowTools,
  ...integrationTools
];

// Create tool registry
const toolRegistry = new Map(
  allTools.map(tool => [tool.name, tool])
);

// Create server instance
const server = new Server(
  {
    name: 'google-cloud-instabids',
    version: '1.0.0',
    description: 'Google Cloud MCP Server for InstaBids AI Hub - Autonomous Infrastructure Management'
  },
  {
    capabilities: {
      tools: {},
      resources: {},
      prompts: {}
    }
  }
);

// Handle list tools request
server.setRequestHandler(ListToolsRequestSchema, async () => {
  logger.info('Listing available tools');
  
  return {
    tools: Array.from(toolRegistry.values()).map(tool => ({
      name: tool.name,
      description: tool.description,
      inputSchema: tool.inputSchema
    }))
  };
});

// Handle tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  logger.info(`Executing tool: ${name}`, { args });
  
  const tool = toolRegistry.get(name);
  if (!tool) {
    throw new Error(`Tool not found: ${name}`);
  }
  
  try {
    // Validate arguments
    const validatedArgs = tool.inputSchema.parse(args);
    
    // Execute tool
    const result = await tool.execute(validatedArgs);
    
    logger.info(`Tool execution successful: ${name}`, { result });
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  } catch (error) {
    logger.error(`Tool execution failed: ${name}`, { error });
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error',
            tool: name
          })
        }
      ],
      isError: true
    };
  }
});

// Error handling
server.onerror = (error) => {
  logger.error('Server error:', error);
};

// Start server
async function main() {
  logger.info('Starting Google Cloud MCP Server for InstaBids AI Hub');
  
  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  logger.info('Server started successfully');
  
  // Handle shutdown
  process.on('SIGINT', async () => {
    logger.info('Shutting down server');
    await server.close();
    process.exit(0);
  });
}

main().catch((error) => {
  logger.error('Failed to start server:', error);
  process.exit(1);
});

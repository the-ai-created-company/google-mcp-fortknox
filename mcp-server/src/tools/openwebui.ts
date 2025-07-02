import { z } from 'zod';
import { CloudRunServiceClient } from '@google-cloud/run';
import { CloudSQLAdminClient } from '@google-cloud/sql';
import { Storage } from '@google-cloud/storage';
import axios from 'axios';
import { MCPTool, ToolResponse } from '../types.js';

const cloudRun = new CloudRunServiceClient();
const cloudSQL = new CloudSQLAdminClient();
const storage = new Storage();

// Deploy Open WebUI Tool
const deployOpenWebUI: MCPTool = {
  name: 'deploy_open_webui',
  description: 'Deploy Open WebUI instance with MCP integration to Google Cloud Run',
  inputSchema: z.object({
    instanceName: z.string(),
    databaseUrl: z.string(),
    redisUrl: z.string().optional(),
    mcpServers: z.array(z.object({
      name: z.string(),
      url: z.string(),
      apiKey: z.string().optional()
    })),
    region: z.string().optional(),
    customDomain: z.string().optional()
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { instanceName, databaseUrl, redisUrl, mcpServers, region = 'us-central1', customDomain } = args;
      const projectId = process.env.GOOGLE_CLOUD_PROJECT;
      
      // Create Open WebUI configuration
      const config = {
        DATABASE_URL: databaseUrl,
        REDIS_URL: redisUrl,
        MCP_ENABLED: 'true',
        MCP_SERVERS: JSON.stringify(mcpServers),
        WEBUI_SECRET_KEY: generateSecretKey(),
        WEBUI_NAME: instanceName,
        ENABLE_SIGNUP: 'false',
        DEFAULT_MODELS: 'gpt-4,claude-3-opus',
        ENABLE_COMMUNITY_SHARING: 'true'
      };
      
      // Deploy to Cloud Run
      const [service] = await cloudRun.createService({
        parent: `projects/${projectId}/locations/${region}`,
        service: {
          metadata: {
            name: `openwebui-${instanceName.toLowerCase()}`,
            annotations: {
              'run.googleapis.com/ingress': 'all',
              'run.googleapis.com/execution-environment': 'gen2'
            }
          },
          spec: {
            template: {
              metadata: {
                annotations: {
                  'autoscaling.knative.dev/minScale': '1',
                  'autoscaling.knative.dev/maxScale': '100',
                  'run.googleapis.com/cpu-throttling': 'false'
                }
              },
              spec: {
                containers: [{
                  image: 'ghcr.io/open-webui/open-webui:main',
                  env: Object.entries(config).map(([name, value]) => ({
                    name,
                    value: String(value)
                  })),
                  resources: {
                    limits: {
                      cpu: '4',
                      memory: '8Gi'
                    }
                  },
                  ports: [{
                    containerPort: 8080
                  }],
                  volumeMounts: [{
                    name: 'data',
                    mountPath: '/app/backend/data'
                  }]
                }],
                volumes: [{
                  name: 'data',
                  emptyDir: {
                    sizeLimit: '10Gi'
                  }
                }]
              }
            }
          }
        }
      });
      
      const serviceUrl = service.status?.url;
      
      // Set up custom domain if provided
      if (customDomain) {
        // TODO: Configure domain mapping
      }
      
      return {
        success: true,
        data: {
          instanceName,
          serviceUrl,
          customDomain,
          status: 'deployed',
          mcpServers: mcpServers.length
        },
        metadata: {
          projectId,
          region,
          timestamp: new Date().toISOString()
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        details: error
      };
    }
  }
};

// Configure Open WebUI MCP Integration Tool
const configureOpenWebUIMCP: MCPTool = {
  name: 'configure_openwebui_mcp',
  description: 'Configure MCP servers and tools in Open WebUI instance',
  inputSchema: z.object({
    instanceUrl: z.string().url(),
    adminToken: z.string(),
    mcpConfiguration: z.object({
      servers: z.array(z.object({
        name: z.string(),
        endpoint: z.string(),
        apiKey: z.string().optional(),
        enabled: z.boolean().optional()
      })),
      defaultTools: z.array(z.string()).optional(),
      autoDiscoverTools: z.boolean().optional()
    })
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { instanceUrl, adminToken, mcpConfiguration } = args;
      
      // Connect to Open WebUI API
      const apiClient = axios.create({
        baseURL: `${instanceUrl}/api/v1`,
        headers: {
          'Authorization': `Bearer ${adminToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      // Update MCP configuration
      const response = await apiClient.post('/admin/mcp/configure', {
        servers: mcpConfiguration.servers,
        settings: {
          defaultTools: mcpConfiguration.defaultTools || [],
          autoDiscoverTools: mcpConfiguration.autoDiscoverTools !== false,
          refreshInterval: 300 // 5 minutes
        }
      });
      
      // Trigger tool discovery
      if (mcpConfiguration.autoDiscoverTools !== false) {
        await apiClient.post('/admin/mcp/discover');
      }
      
      return {
        success: true,
        data: {
          configured: true,
          serversConfigured: mcpConfiguration.servers.length,
          toolsDiscovered: response.data.toolsDiscovered || 0
        },
        metadata: {
          instanceUrl,
          timestamp: new Date().toISOString()
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        details: error
      };
    }
  }
};

// Create Open WebUI Agent Tool
const createOpenWebUIAgent: MCPTool = {
  name: 'create_openwebui_agent',
  description: 'Create an autonomous agent within Open WebUI',
  inputSchema: z.object({
    instanceUrl: z.string().url(),
    adminToken: z.string(),
    agentConfig: z.object({
      name: z.string(),
      description: z.string(),
      model: z.string(),
      systemPrompt: z.string(),
      tools: z.array(z.string()),
      temperature: z.number().optional(),
      maxTokens: z.number().optional(),
      capabilities: z.array(z.enum(['web_search', 'code_execution', 'file_access', 'api_calls'])).optional()
    })
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { instanceUrl, adminToken, agentConfig } = args;
      
      const apiClient = axios.create({
        baseURL: `${instanceUrl}/api/v1`,
        headers: {
          'Authorization': `Bearer ${adminToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      // Create agent in Open WebUI
      const response = await apiClient.post('/agents', {
        name: agentConfig.name,
        description: agentConfig.description,
        config: {
          model: agentConfig.model,
          system_prompt: agentConfig.systemPrompt,
          temperature: agentConfig.temperature || 0.7,
          max_tokens: agentConfig.maxTokens || 4096,
          tools: agentConfig.tools,
          capabilities: agentConfig.capabilities || ['web_search', 'api_calls']
        }
      });
      
      const agentId = response.data.id;
      
      // Enable the agent
      await apiClient.patch(`/agents/${agentId}`, {
        enabled: true
      });
      
      return {
        success: true,
        data: {
          agentId,
          name: agentConfig.name,
          status: 'created',
          endpoint: `${instanceUrl}/agents/${agentId}`
        },
        metadata: {
          instanceUrl,
          timestamp: new Date().toISOString()
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        details: error
      };
    }
  }
};

// Sync MCP Tools with Open WebUI Tool
const syncMCPToolsWithOpenWebUI: MCPTool = {
  name: 'sync_mcp_tools_openwebui',
  description: 'Synchronize all MCP tools with Open WebUI instance',
  inputSchema: z.object({
    instanceUrl: z.string().url(),
    adminToken: z.string(),
    toolFilter: z.object({
      categories: z.array(z.string()).optional(),
      includePattern: z.string().optional(),
      excludePattern: z.string().optional()
    }).optional()
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { instanceUrl, adminToken, toolFilter } = args;
      
      // Get all available MCP tools
      const toolsBucket = storage.bucket('instabids-mcp-tools');
      const [files] = await toolsBucket.getFiles();
      const tools = [];
      
      for (const file of files.filter(f => f.name.endsWith('metadata.json'))) {
        const [content] = await file.download();
        const metadata = JSON.parse(content.toString());
        
        // Apply filters
        if (toolFilter?.categories && !toolFilter.categories.includes(metadata.category)) continue;
        if (toolFilter?.includePattern && !metadata.name.match(toolFilter.includePattern)) continue;
        if (toolFilter?.excludePattern && metadata.name.match(toolFilter.excludePattern)) continue;
        
        tools.push({
          id: metadata.id,
          name: metadata.name,
          description: metadata.description,
          category: metadata.category,
          inputSchema: metadata.inputSchema
        });
      }
      
      // Sync tools with Open WebUI
      const apiClient = axios.create({
        baseURL: `${instanceUrl}/api/v1`,
        headers: {
          'Authorization': `Bearer ${adminToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      const syncResults = await apiClient.post('/admin/tools/sync', {
        tools,
        updateExisting: true,
        removeDeleted: false
      });
      
      return {
        success: true,
        data: {
          totalTools: tools.length,
          synced: syncResults.data.synced || tools.length,
          added: syncResults.data.added || 0,
          updated: syncResults.data.updated || 0,
          failed: syncResults.data.failed || 0
        },
        metadata: {
          instanceUrl,
          timestamp: new Date().toISOString()
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        details: error
      };
    }
  }
};

// Monitor Open WebUI Health Tool
const monitorOpenWebUIHealth: MCPTool = {
  name: 'monitor_openwebui_health',
  description: 'Monitor health and performance of Open WebUI instance',
  inputSchema: z.object({
    instanceUrl: z.string().url(),
    adminToken: z.string(),
    metrics: z.array(z.enum(['cpu', 'memory', 'requests', 'errors', 'agents', 'tools'])).optional()
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { instanceUrl, adminToken, metrics = ['cpu', 'memory', 'requests', 'agents'] } = args;
      
      const apiClient = axios.create({
        baseURL: `${instanceUrl}/api/v1`,
        headers: {
          'Authorization': `Bearer ${adminToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      // Get health metrics
      const healthResponse = await apiClient.get('/health');
      const metricsResponse = await apiClient.get('/admin/metrics');
      
      const healthData = {
        status: healthResponse.data.status,
        uptime: healthResponse.data.uptime,
        version: healthResponse.data.version
      };
      
      const metricsData = {};
      
      if (metrics.includes('cpu')) {
        metricsData['cpu'] = metricsResponse.data.cpu || { usage: 0 };
      }
      
      if (metrics.includes('memory')) {
        metricsData['memory'] = metricsResponse.data.memory || { usage: 0, total: 0 };
      }
      
      if (metrics.includes('requests')) {
        metricsData['requests'] = metricsResponse.data.requests || { total: 0, rate: 0 };
      }
      
      if (metrics.includes('errors')) {
        metricsData['errors'] = metricsResponse.data.errors || { total: 0, rate: 0 };
      }
      
      if (metrics.includes('agents')) {
        const agentsResponse = await apiClient.get('/admin/agents/stats');
        metricsData['agents'] = agentsResponse.data || { total: 0, active: 0 };
      }
      
      if (metrics.includes('tools')) {
        const toolsResponse = await apiClient.get('/admin/tools/stats');
        metricsData['tools'] = toolsResponse.data || { total: 0, enabled: 0 };
      }
      
      return {
        success: true,
        data: {
          health: healthData,
          metrics: metricsData
        },
        metadata: {
          instanceUrl,
          timestamp: new Date().toISOString()
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        details: error
      };
    }
  }
};

// Helper function to generate secret key
function generateSecretKey(): string {
  return require('crypto').randomBytes(32).toString('hex');
}

export const openwebuiTools: MCPTool[] = [
  deployOpenWebUI,
  configureOpenWebUIMCP,
  createOpenWebUIAgent,
  syncMCPToolsWithOpenWebUI,
  monitorOpenWebUIHealth
];

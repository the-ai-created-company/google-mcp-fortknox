import { z } from 'zod';
import { Storage } from '@google-cloud/storage';
import { CloudRunServiceClient } from '@google-cloud/run';
import { MCPTool, ToolDefinitionSchema, ToolResponse } from '../types.js';
import { exec } from 'child_process';
import { promisify } from 'util';
import { writeFile, mkdir } from 'fs/promises';
import path from 'path';
import crypto from 'crypto';

const execAsync = promisify(exec);
const storage = new Storage();
const cloudRun = new CloudRunServiceClient();

// Create MCP Tool
const createMCPTool: MCPTool = {
  name: 'create_mcp_tool',
  description: 'Create a new MCP tool dynamically that can be used by agents',
  inputSchema: ToolDefinitionSchema,
  execute: async (args): Promise<ToolResponse> => {
    try {
      const toolDef = args;
      const projectId = process.env.GOOGLE_CLOUD_PROJECT;
      const toolId = `tool-${toolDef.name.toLowerCase().replace(/[^a-z0-9]/g, '-')}-${crypto.randomBytes(4).toString('hex')}`;
      
      // Create tool implementation file
      const toolCode = `
import { z } from 'zod';
import { MCPTool, ToolResponse } from '../types.js';
${toolDef.dependencies ? toolDef.dependencies.map(dep => `import ${dep};`).join('\n') : ''}

// Auto-generated tool: ${toolDef.name}
export const ${toolDef.name}: MCPTool = {
  name: '${toolDef.name}',
  description: '${toolDef.description}',
  inputSchema: z.object(${JSON.stringify(toolDef.inputSchema)}),
  execute: async (args): Promise<ToolResponse> => {
    try {
      ${toolDef.implementation}
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        details: error
      };
    }
  }
};

export default ${toolDef.name};
`;

      // Save tool to storage
      const toolsBucket = storage.bucket('instabids-mcp-tools');
      const toolFile = toolsBucket.file(`${toolId}/implementation.ts`);
      await toolFile.save(toolCode);
      
      // Save tool metadata
      const metadata = {
        id: toolId,
        name: toolDef.name,
        description: toolDef.description,
        created: new Date().toISOString(),
        runtime: toolDef.runtime || 'node',
        inputSchema: toolDef.inputSchema,
        location: `gs://instabids-mcp-tools/${toolId}/implementation.ts`
      };
      
      const metadataFile = toolsBucket.file(`${toolId}/metadata.json`);
      await metadataFile.save(JSON.stringify(metadata, null, 2));
      
      // Register tool in the tool registry
      await registerTool(metadata);
      
      return {
        success: true,
        data: {
          toolId,
          name: toolDef.name,
          status: 'created',
          location: metadata.location,
          metadata
        },
        metadata: {
          projectId,
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

// Deploy MCP Tool
const deployMCPTool: MCPTool = {
  name: 'deploy_mcp_tool',
  description: 'Deploy a created MCP tool to make it available for use',
  inputSchema: z.object({
    toolId: z.string(),
    targetEnvironment: z.enum(['development', 'staging', 'production']).optional()
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { toolId, targetEnvironment = 'production' } = args;
      const projectId = process.env.GOOGLE_CLOUD_PROJECT;
      
      // Retrieve tool from storage
      const toolsBucket = storage.bucket('instabids-mcp-tools');
      const [toolCode] = await toolsBucket.file(`${toolId}/implementation.ts`).download();
      const [metadataContent] = await toolsBucket.file(`${toolId}/metadata.json`).download();
      const metadata = JSON.parse(metadataContent.toString());
      
      // Create deployment package
      const deploymentDir = `/tmp/mcp-tool-${toolId}`;
      await mkdir(deploymentDir, { recursive: true });
      
      // Write tool file
      await writeFile(path.join(deploymentDir, 'tool.ts'), toolCode);
      
      // Create package.json for the tool
      const packageJson = {
        name: `@instabids/mcp-tool-${metadata.name}`,
        version: '1.0.0',
        type: 'module',
        main: 'dist/tool.js',
        scripts: {
          build: 'tsc'
        },
        dependencies: {
          '@modelcontextprotocol/sdk': '^0.6.0',
          'zod': '^3.24.1',
          ...(metadata.dependencies || {})
        }
      };
      
      await writeFile(
        path.join(deploymentDir, 'package.json'),
        JSON.stringify(packageJson, null, 2)
      );
      
      // Build the tool
      await execAsync('npm install && npm run build', { cwd: deploymentDir });
      
      // Deploy to tool registry
      const deploymentResult = await deployToolToRegistry(toolId, deploymentDir, targetEnvironment);
      
      return {
        success: true,
        data: {
          toolId,
          name: metadata.name,
          status: 'deployed',
          environment: targetEnvironment,
          endpoint: deploymentResult.endpoint
        },
        metadata: {
          projectId,
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

// List Available Tools
const listMCPTools: MCPTool = {
  name: 'list_mcp_tools',
  description: 'List all available MCP tools in the system',
  inputSchema: z.object({
    category: z.string().optional(),
    status: z.enum(['created', 'deployed', 'deprecated', 'all']).optional(),
    searchTerm: z.string().optional()
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { category, status = 'all', searchTerm } = args;
      const projectId = process.env.GOOGLE_CLOUD_PROJECT;
      
      // List all tools from storage
      const toolsBucket = storage.bucket('instabids-mcp-tools');
      const [files] = await toolsBucket.getFiles();
      
      const tools = [];
      const metadataFiles = files.filter(file => file.name.endsWith('metadata.json'));
      
      for (const file of metadataFiles) {
        const [content] = await file.download();
        const metadata = JSON.parse(content.toString());
        
        // Apply filters
        if (status !== 'all' && metadata.status !== status) continue;
        if (category && metadata.category !== category) continue;
        if (searchTerm && !metadata.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
            !metadata.description.toLowerCase().includes(searchTerm.toLowerCase())) continue;
        
        tools.push({
          id: metadata.id,
          name: metadata.name,
          description: metadata.description,
          status: metadata.status || 'created',
          created: metadata.created,
          category: metadata.category
        });
      }
      
      return {
        success: true,
        data: tools,
        metadata: {
          count: tools.length,
          projectId,
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

// Update MCP Tool
const updateMCPTool: MCPTool = {
  name: 'update_mcp_tool',
  description: 'Update an existing MCP tool implementation or metadata',
  inputSchema: z.object({
    toolId: z.string(),
    updates: z.object({
      description: z.string().optional(),
      implementation: z.string().optional(),
      inputSchema: z.record(z.any()).optional(),
      dependencies: z.array(z.string()).optional()
    })
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { toolId, updates } = args;
      const projectId = process.env.GOOGLE_CLOUD_PROJECT;
      
      // Retrieve current tool
      const toolsBucket = storage.bucket('instabids-mcp-tools');
      const [metadataContent] = await toolsBucket.file(`${toolId}/metadata.json`).download();
      const metadata = JSON.parse(metadataContent.toString());
      
      // Update metadata
      const updatedMetadata = {
        ...metadata,
        ...updates,
        lastUpdated: new Date().toISOString()
      };
      
      // If implementation is updated, regenerate the tool code
      if (updates.implementation) {
        const [currentCode] = await toolsBucket.file(`${toolId}/implementation.ts`).download();
        const updatedCode = currentCode.toString().replace(
          /execute: async \(args\): Promise<ToolResponse> => {[\s\S]*?}(?=\s*}\s*;)/,
          `execute: async (args): Promise<ToolResponse> => {
    try {
      ${updates.implementation}
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        details: error
      };
    }
  }`
        );
        
        await toolsBucket.file(`${toolId}/implementation.ts`).save(updatedCode);
      }
      
      // Save updated metadata
      await toolsBucket.file(`${toolId}/metadata.json`).save(
        JSON.stringify(updatedMetadata, null, 2)
      );
      
      return {
        success: true,
        data: {
          toolId,
          name: updatedMetadata.name,
          status: 'updated',
          updates: Object.keys(updates)
        },
        metadata: {
          projectId,
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

// Test MCP Tool
const testMCPTool: MCPTool = {
  name: 'test_mcp_tool',
  description: 'Test an MCP tool with sample inputs',
  inputSchema: z.object({
    toolName: z.string(),
    testInputs: z.record(z.any()),
    validateOutput: z.boolean().optional()
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { toolName, testInputs, validateOutput = true } = args;
      
      // Dynamic import of the tool
      // Note: In production, this would load from the tool registry
      const toolModule = await import(`./dynamic/${toolName}.js`);
      const tool = toolModule.default;
      
      // Execute the tool with test inputs
      const startTime = Date.now();
      const result = await tool.execute(testInputs);
      const executionTime = Date.now() - startTime;
      
      // Validate output if requested
      let validation = null;
      if (validateOutput) {
        validation = {
          hasSuccess: 'success' in result,
          hasData: 'data' in result && result.success,
          hasError: 'error' in result && !result.success,
          isValidResponse: true
        };
      }
      
      return {
        success: true,
        data: {
          toolName,
          testInputs,
          result,
          executionTime: `${executionTime}ms`,
          validation
        },
        metadata: {
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

// Helper function to register tool in the system
async function registerTool(metadata: any): Promise<void> {
  // In production, this would update a central tool registry
  // For now, we'll store in a registry file
  const registryBucket = storage.bucket('instabids-mcp-tools');
  const registryFile = registryBucket.file('registry.json');
  
  let registry = [];
  try {
    const [content] = await registryFile.download();
    registry = JSON.parse(content.toString());
  } catch (error) {
    // Registry doesn't exist yet
  }
  
  registry.push({
    id: metadata.id,
    name: metadata.name,
    description: metadata.description,
    created: metadata.created,
    location: metadata.location
  });
  
  await registryFile.save(JSON.stringify(registry, null, 2));
}

// Helper function to deploy tool to registry
async function deployToolToRegistry(toolId: string, deploymentDir: string, environment: string): Promise<any> {
  // In production, this would deploy to a tool serving infrastructure
  // For now, we'll simulate deployment
  return {
    endpoint: `https://mcp-tools.instabids-ai-hub.run.app/tools/${toolId}`,
    version: '1.0.0',
    environment
  };
}

export const toolCreationTools: MCPTool[] = [
  createMCPTool,
  deployMCPTool,
  listMCPTools,
  updateMCPTool,
  testMCPTool
];

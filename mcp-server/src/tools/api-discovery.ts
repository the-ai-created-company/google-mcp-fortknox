import { z } from 'zod';
import axios from 'axios';
import { Storage } from '@google-cloud/storage';
import { MCPTool, APISpecSchema, ToolResponse } from '../types.js';
import { parse as parseOpenAPI } from 'openapi-parser';
import { buildSchema as parseGraphQL } from 'graphql';

const storage = new Storage();

// Discover API Tool
const discoverAPI: MCPTool = {
  name: 'discover_api',
  description: 'Discover and analyze an API to understand its endpoints and create integration tools',
  inputSchema: z.object({
    apiUrl: z.string().url(),
    authMethod: z.enum(['none', 'api_key', 'bearer', 'basic', 'oauth2']).optional(),
    authCredentials: z.record(z.string()).optional(),
    apiType: z.enum(['rest', 'graphql', 'grpc', 'auto']).optional()
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { apiUrl, authMethod = 'none', authCredentials, apiType = 'auto' } = args;
      
      // Try to find API documentation
      const discoveryResults = {
        baseUrl: new URL(apiUrl).origin,
        endpoints: [],
        authentication: authMethod,
        apiType: apiType,
        documentation: null
      };
      
      // Check for common API documentation endpoints
      const docEndpoints = [
        '/openapi.json',
        '/swagger.json',
        '/api-docs',
        '/v1/api-docs',
        '/v2/api-docs',
        '/v3/api-docs',
        '/.well-known/openapi.json',
        '/graphql/schema',
        '/graphql',
        '/_schema'
      ];
      
      for (const endpoint of docEndpoints) {
        try {
          const response = await axios.get(`${discoveryResults.baseUrl}${endpoint}`, {
            headers: getAuthHeaders(authMethod, authCredentials),
            timeout: 5000
          });
          
          if (response.data) {
            // Detect API type from response
            if (response.data.openapi || response.data.swagger) {
              discoveryResults.apiType = 'rest';
              discoveryResults.documentation = response.data;
              break;
            } else if (response.data.__schema || response.data.data?.__schema) {
              discoveryResults.apiType = 'graphql';
              discoveryResults.documentation = response.data;
              break;
            }
          }
        } catch (error) {
          // Continue trying other endpoints
        }
      }
      
      // If no documentation found, try to probe the API
      if (!discoveryResults.documentation && apiType === 'auto') {
        discoveryResults.endpoints = await probeAPIEndpoints(apiUrl, authMethod, authCredentials);
      }
      
      // Parse discovered documentation
      if (discoveryResults.documentation) {
        if (discoveryResults.apiType === 'rest') {
          const parsed = await parseOpenAPIDoc(discoveryResults.documentation);
          discoveryResults.endpoints = parsed.endpoints;
        } else if (discoveryResults.apiType === 'graphql') {
          const parsed = parseGraphQLSchema(discoveryResults.documentation);
          discoveryResults.endpoints = parsed.operations;
        }
      }
      
      // Store discovery results
      const apiId = `api-${new URL(apiUrl).hostname.replace(/\./g, '-')}-${Date.now()}`;
      const apiBucket = storage.bucket('instabids-api-discoveries');
      await apiBucket.file(`${apiId}/discovery.json`).save(
        JSON.stringify(discoveryResults, null, 2)
      );
      
      return {
        success: true,
        data: {
          apiId,
          baseUrl: discoveryResults.baseUrl,
          apiType: discoveryResults.apiType,
          endpointsFound: discoveryResults.endpoints.length,
          hasDocumentation: !!discoveryResults.documentation,
          endpoints: discoveryResults.endpoints.slice(0, 10) // First 10 endpoints
        },
        metadata: {
          storageLocation: `gs://instabids-api-discoveries/${apiId}/discovery.json`,
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

// Generate API Wrapper Tool
const generateAPIWrapper: MCPTool = {
  name: 'generate_api_wrapper',
  description: 'Generate MCP tool wrappers for discovered API endpoints',
  inputSchema: z.object({
    apiId: z.string(),
    endpoints: z.array(z.string()).optional(),
    wrapperName: z.string()
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { apiId, endpoints, wrapperName } = args;
      
      // Retrieve API discovery data
      const apiBucket = storage.bucket('instabids-api-discoveries');
      const [discoveryData] = await apiBucket.file(`${apiId}/discovery.json`).download();
      const discovery = JSON.parse(discoveryData.toString());
      
      // Select endpoints to wrap
      const endpointsToWrap = endpoints || discovery.endpoints.map(e => e.path || e.name);
      
      // Generate wrapper tools
      const wrapperTools = [];
      
      for (const endpoint of discovery.endpoints) {
        if (!endpointsToWrap.includes(endpoint.path || endpoint.name)) continue;
        
        const toolCode = generateToolCode(endpoint, discovery, wrapperName);
        wrapperTools.push(toolCode);
      }
      
      // Create wrapper module
      const wrapperModule = `
import { z } from 'zod';
import axios from 'axios';
import { MCPTool, ToolResponse } from '../types.js';

const baseUrl = '${discovery.baseUrl}';
const authMethod = '${discovery.authentication}';

${wrapperTools.join('\n\n')}

export const ${wrapperName}Tools: MCPTool[] = [
  ${wrapperTools.map(t => t.name).join(',\n  ')}
];
`;
      
      // Save wrapper
      const wrapperId = `wrapper-${wrapperName}-${Date.now()}`;
      await apiBucket.file(`${apiId}/wrappers/${wrapperId}.ts`).save(wrapperModule);
      
      return {
        success: true,
        data: {
          wrapperId,
          wrapperName,
          toolsGenerated: wrapperTools.length,
          location: `gs://instabids-api-discoveries/${apiId}/wrappers/${wrapperId}.ts`
        },
        metadata: {
          apiId,
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

// Test API Endpoint Tool
const testAPIEndpoint: MCPTool = {
  name: 'test_api_endpoint',
  description: 'Test an API endpoint with sample data',
  inputSchema: z.object({
    url: z.string().url(),
    method: z.enum(['GET', 'POST', 'PUT', 'DELETE', 'PATCH']),
    headers: z.record(z.string()).optional(),
    body: z.any().optional(),
    queryParams: z.record(z.string()).optional()
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { url, method, headers = {}, body, queryParams } = args;
      
      const response = await axios({
        url,
        method,
        headers,
        data: body,
        params: queryParams,
        timeout: 30000,
        validateStatus: () => true // Don't throw on HTTP errors
      });
      
      return {
        success: true,
        data: {
          status: response.status,
          statusText: response.statusText,
          headers: response.headers,
          data: response.data,
          responseTime: response.headers['x-response-time'] || 'N/A'
        },
        metadata: {
          url,
          method,
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

// Monitor API Health Tool
const monitorAPIHealth: MCPTool = {
  name: 'monitor_api_health',
  description: 'Set up monitoring for API endpoints',
  inputSchema: z.object({
    apiId: z.string(),
    endpoints: z.array(z.object({
      url: z.string(),
      method: z.string(),
      expectedStatus: z.number().optional(),
      timeout: z.number().optional()
    })),
    interval: z.string().optional() // e.g., "5m", "1h"
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { apiId, endpoints, interval = '5m' } = args;
      
      // Create monitoring configuration
      const monitorConfig = {
        apiId,
        endpoints: endpoints.map(ep => ({
          ...ep,
          expectedStatus: ep.expectedStatus || 200,
          timeout: ep.timeout || 5000
        })),
        interval,
        created: new Date().toISOString(),
        status: 'active'
      };
      
      // Store monitoring configuration
      const monitoringBucket = storage.bucket('instabids-api-monitoring');
      const monitorId = `monitor-${apiId}-${Date.now()}`;
      await monitoringBucket.file(`${monitorId}/config.json`).save(
        JSON.stringify(monitorConfig, null, 2)
      );
      
      // TODO: Set up actual monitoring with Cloud Scheduler
      
      return {
        success: true,
        data: {
          monitorId,
          apiId,
          endpointsMonitored: endpoints.length,
          interval,
          status: 'configured'
        },
        metadata: {
          configLocation: `gs://instabids-api-monitoring/${monitorId}/config.json`,
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

// Create API Documentation Tool
const createAPIDocumentation: MCPTool = {
  name: 'create_api_documentation',
  description: 'Generate documentation for discovered APIs',
  inputSchema: z.object({
    apiId: z.string(),
    format: z.enum(['markdown', 'openapi', 'postman']).optional(),
    includeExamples: z.boolean().optional()
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { apiId, format = 'markdown', includeExamples = true } = args;
      
      // Retrieve API discovery data
      const apiBucket = storage.bucket('instabids-api-discoveries');
      const [discoveryData] = await apiBucket.file(`${apiId}/discovery.json`).download();
      const discovery = JSON.parse(discoveryData.toString());
      
      let documentation;
      
      switch (format) {
        case 'markdown':
          documentation = generateMarkdownDoc(discovery, includeExamples);
          break;
        case 'openapi':
          documentation = generateOpenAPIDoc(discovery);
          break;
        case 'postman':
          documentation = generatePostmanCollection(discovery);
          break;
      }
      
      // Save documentation
      const docFile = apiBucket.file(`${apiId}/documentation.${format}`);
      await docFile.save(
        typeof documentation === 'string' ? documentation : JSON.stringify(documentation, null, 2)
      );
      
      return {
        success: true,
        data: {
          apiId,
          format,
          location: `gs://instabids-api-discoveries/${apiId}/documentation.${format}`,
          size: Buffer.byteLength(typeof documentation === 'string' ? documentation : JSON.stringify(documentation))
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

// Helper Functions

function getAuthHeaders(authMethod: string, credentials?: Record<string, string>): Record<string, string> {
  const headers: Record<string, string> = {};
  
  switch (authMethod) {
    case 'api_key':
      if (credentials?.key && credentials?.header) {
        headers[credentials.header] = credentials.key;
      }
      break;
    case 'bearer':
      if (credentials?.token) {
        headers['Authorization'] = `Bearer ${credentials.token}`;
      }
      break;
    case 'basic':
      if (credentials?.username && credentials?.password) {
        const encoded = Buffer.from(`${credentials.username}:${credentials.password}`).toString('base64');
        headers['Authorization'] = `Basic ${encoded}`;
      }
      break;
  }
  
  return headers;
}

async function probeAPIEndpoints(baseUrl: string, authMethod: string, credentials?: Record<string, string>): Promise<any[]> {
  const commonEndpoints = [
    '/',
    '/api',
    '/v1',
    '/v2',
    '/health',
    '/status',
    '/info',
    '/users',
    '/auth',
    '/products',
    '/items'
  ];
  
  const discovered = [];
  
  for (const endpoint of commonEndpoints) {
    try {
      const response = await axios.get(`${baseUrl}${endpoint}`, {
        headers: getAuthHeaders(authMethod, credentials),
        timeout: 3000,
        validateStatus: () => true
      });
      
      if (response.status < 500) {
        discovered.push({
          path: endpoint,
          method: 'GET',
          status: response.status,
          contentType: response.headers['content-type']
        });
      }
    } catch (error) {
      // Skip failed endpoints
    }
  }
  
  return discovered;
}

async function parseOpenAPIDoc(doc: any): Promise<any> {
  const endpoints = [];
  const paths = doc.paths || {};
  
  for (const [path, methods] of Object.entries(paths)) {
    for (const [method, spec] of Object.entries(methods as any)) {
      if (['get', 'post', 'put', 'delete', 'patch'].includes(method)) {
        endpoints.push({
          path,
          method: method.toUpperCase(),
          summary: spec.summary || '',
          description: spec.description || '',
          parameters: spec.parameters || [],
          requestBody: spec.requestBody || null,
          responses: spec.responses || {}
        });
      }
    }
  }
  
  return { endpoints };
}

function parseGraphQLSchema(schema: any): any {
  // Simplified GraphQL parsing
  const operations = [];
  
  if (schema.__schema || schema.data?.__schema) {
    const schemaData = schema.__schema || schema.data.__schema;
    const queryType = schemaData.queryType;
    const mutationType = schemaData.mutationType;
    
    // Extract queries and mutations
    // This is a simplified version - full implementation would be more complex
  }
  
  return { operations };
}

function generateToolCode(endpoint: any, discovery: any, wrapperName: string): any {
  const toolName = `${wrapperName}_${endpoint.method.toLowerCase()}_${endpoint.path.replace(/[^a-zA-Z0-9]/g, '_')}`;
  
  return {
    name: toolName,
    code: `
const ${toolName}: MCPTool = {
  name: '${toolName}',
  description: '${endpoint.summary || endpoint.description || `${endpoint.method} ${endpoint.path}`}',
  inputSchema: z.object({
    ${generateInputSchema(endpoint)}
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const response = await axios({
        url: \`\${baseUrl}${endpoint.path}\`,
        method: '${endpoint.method}',
        headers: getAuthHeaders(authMethod, args.authCredentials),
        data: args.body,
        params: args.queryParams
      });
      
      return {
        success: true,
        data: response.data,
        metadata: {
          status: response.status,
          headers: response.headers
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
};`
  };
}

function generateInputSchema(endpoint: any): string {
  const schema = [];
  
  if (endpoint.parameters) {
    const queryParams = endpoint.parameters.filter(p => p.in === 'query');
    const pathParams = endpoint.parameters.filter(p => p.in === 'path');
    
    if (queryParams.length > 0) {
      schema.push('queryParams: z.record(z.string()).optional()');
    }
    
    for (const param of pathParams) {
      schema.push(`${param.name}: z.string()`);
    }
  }
  
  if (endpoint.requestBody) {
    schema.push('body: z.any().optional()');
  }
  
  schema.push('authCredentials: z.record(z.string()).optional()');
  
  return schema.join(',\n    ');
}

function generateMarkdownDoc(discovery: any, includeExamples: boolean): string {
  let doc = `# API Documentation: ${discovery.baseUrl}\n\n`;
  doc += `**Type**: ${discovery.apiType}\n`;
  doc += `**Authentication**: ${discovery.authentication}\n\n`;
  
  doc += `## Endpoints\n\n`;
  
  for (const endpoint of discovery.endpoints) {
    doc += `### ${endpoint.method} ${endpoint.path}\n\n`;
    if (endpoint.summary) doc += `${endpoint.summary}\n\n`;
    if (endpoint.description) doc += `${endpoint.description}\n\n`;
    
    if (includeExamples) {
      doc += `**Example Request**:\n\`\`\`bash\ncurl -X ${endpoint.method} ${discovery.baseUrl}${endpoint.path}\n\`\`\`\n\n`;
    }
  }
  
  return doc;
}

function generateOpenAPIDoc(discovery: any): any {
  return {
    openapi: '3.0.0',
    info: {
      title: `API Documentation for ${discovery.baseUrl}`,
      version: '1.0.0'
    },
    servers: [{ url: discovery.baseUrl }],
    paths: discovery.endpoints.reduce((paths, endpoint) => {
      if (!paths[endpoint.path]) paths[endpoint.path] = {};
      paths[endpoint.path][endpoint.method.toLowerCase()] = {
        summary: endpoint.summary,
        description: endpoint.description,
        parameters: endpoint.parameters || [],
        responses: endpoint.responses || { '200': { description: 'Success' } }
      };
      return paths;
    }, {})
  };
}

function generatePostmanCollection(discovery: any): any {
  return {
    info: {
      name: `${discovery.baseUrl} API`,
      schema: 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'
    },
    item: discovery.endpoints.map(endpoint => ({
      name: `${endpoint.method} ${endpoint.path}`,
      request: {
        method: endpoint.method,
        url: {
          raw: `${discovery.baseUrl}${endpoint.path}`,
          host: [discovery.baseUrl],
          path: endpoint.path.split('/').filter(Boolean)
        }
      }
    }))
  };
}

export const apiDiscoveryTools: MCPTool[] = [
  discoverAPI,
  generateAPIWrapper,
  testAPIEndpoint,
  monitorAPIHealth,
  createAPIDocumentation
];

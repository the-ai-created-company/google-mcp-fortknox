import { z } from 'zod';

// Base tool interface
export interface MCPTool {
  name: string;
  description: string;
  inputSchema: z.ZodSchema<any>;
  execute: (args: any) => Promise<any>;
}

// Common response types
export const SuccessResponseSchema = z.object({
  success: z.literal(true),
  data: z.any(),
  metadata: z.record(z.any()).optional()
});

export const ErrorResponseSchema = z.object({
  success: z.literal(false),
  error: z.string(),
  details: z.any().optional()
});

export const ToolResponseSchema = z.union([SuccessResponseSchema, ErrorResponseSchema]);
export type ToolResponse = z.infer<typeof ToolResponseSchema>;

// Infrastructure types
export const ResourceTypeSchema = z.enum([
  'compute_instance',
  'cloud_run_service',
  'gke_cluster',
  'cloud_sql',
  'storage_bucket',
  'vpc_network',
  'load_balancer',
  'firewall_rule',
  'service_account',
  'secret'
]);

export type ResourceType = z.infer<typeof ResourceTypeSchema>;

// Agent types
export const AgentConfigSchema = z.object({
  name: z.string(),
  description: z.string(),
  tools: z.array(z.string()),
  memory: z.object({
    type: z.enum(['redis', 'firestore', 'cloud_sql']),
    config: z.record(z.any())
  }),
  permissions: z.array(z.string()),
  environment: z.record(z.string()).optional()
});

export type AgentConfig = z.infer<typeof AgentConfigSchema>;

// Database types
export const DatabaseTypeSchema = z.enum([
  'postgres',
  'mysql',
  'redis',
  'firestore',
  'bigquery'
]);

export type DatabaseType = z.infer<typeof DatabaseTypeSchema>;

export const DatabaseConfigSchema = z.object({
  name: z.string(),
  type: DatabaseTypeSchema,
  tier: z.string().optional(),
  region: z.string(),
  highAvailability: z.boolean().optional(),
  backups: z.boolean().optional(),
  permissions: z.array(z.object({
    principal: z.string(),
    role: z.string()
  })).optional()
});

export type DatabaseConfig = z.infer<typeof DatabaseConfigSchema>;

// Deployment types
export const DeploymentConfigSchema = z.object({
  name: z.string(),
  image: z.string(),
  region: z.string(),
  cpu: z.string().optional(),
  memory: z.string().optional(),
  minInstances: z.number().optional(),
  maxInstances: z.number().optional(),
  environment: z.record(z.string()).optional(),
  secrets: z.array(z.string()).optional(),
  serviceAccount: z.string().optional()
});

export type DeploymentConfig = z.infer<typeof DeploymentConfigSchema>;

// API Discovery types
export const APISpecSchema = z.object({
  openapi: z.string().optional(),
  swagger: z.string().optional(),
  graphql: z.string().optional(),
  grpc: z.string().optional(),
  custom: z.record(z.any()).optional()
});

export type APISpec = z.infer<typeof APISpecSchema>;

// Tool creation types
export const ToolDefinitionSchema = z.object({
  name: z.string(),
  description: z.string(),
  inputSchema: z.record(z.any()),
  implementation: z.string(), // JavaScript/TypeScript code as string
  dependencies: z.array(z.string()).optional(),
  runtime: z.enum(['node', 'python', 'go']).optional()
});

export type ToolDefinition = z.infer<typeof ToolDefinitionSchema>;

// Monitoring types
export const MetricTypeSchema = z.enum([
  'cpu_usage',
  'memory_usage',
  'request_count',
  'error_rate',
  'latency',
  'custom'
]);

export type MetricType = z.infer<typeof MetricTypeSchema>;

export const AlertConfigSchema = z.object({
  name: z.string(),
  metric: MetricTypeSchema,
  threshold: z.number(),
  comparison: z.enum(['gt', 'lt', 'eq', 'gte', 'lte']),
  duration: z.string(), // e.g., "5m", "1h"
  notificationChannels: z.array(z.string())
});

export type AlertConfig = z.infer<typeof AlertConfigSchema>;

// Workflow types
export const WorkflowStepSchema = z.object({
  name: z.string(),
  tool: z.string(),
  arguments: z.record(z.any()),
  condition: z.string().optional(), // JavaScript expression
  onSuccess: z.string().optional(), // Next step name
  onFailure: z.string().optional(), // Next step name
  retries: z.number().optional()
});

export type WorkflowStep = z.infer<typeof WorkflowStepSchema>;

export const WorkflowDefinitionSchema = z.object({
  name: z.string(),
  description: z.string(),
  steps: z.array(WorkflowStepSchema),
  triggers: z.array(z.enum(['manual', 'schedule', 'event', 'webhook'])),
  schedule: z.string().optional(), // Cron expression
  timeout: z.string().optional() // e.g., "30m"
});

export type WorkflowDefinition = z.infer<typeof WorkflowDefinitionSchema>;

// Project configuration
export interface ProjectConfig {
  projectId: string;
  region: string;
  credentials?: string; // Path to service account JSON
}

// Export all schemas
export const schemas = {
  SuccessResponseSchema,
  ErrorResponseSchema,
  ToolResponseSchema,
  ResourceTypeSchema,
  AgentConfigSchema,
  DatabaseTypeSchema,
  DatabaseConfigSchema,
  DeploymentConfigSchema,
  APISpecSchema,
  ToolDefinitionSchema,
  MetricTypeSchema,
  AlertConfigSchema,
  WorkflowStepSchema,
  WorkflowDefinitionSchema
};

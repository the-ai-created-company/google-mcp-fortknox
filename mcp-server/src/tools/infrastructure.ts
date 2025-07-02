import { z } from 'zod';
import { Compute } from '@google-cloud/compute';
import { Storage } from '@google-cloud/storage';
import { CloudRunServiceClient } from '@google-cloud/run';
import { CloudSQLAdminClient } from '@google-cloud/sql';
import { CloudRedisClient } from '@google-cloud/redis';
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';
import { ResourceManagerServiceClient } from '@google-cloud/resource-manager';
import { MCPTool, ResourceTypeSchema, ToolResponse } from '../types.js';

const compute = new Compute();
const storage = new Storage();
const cloudRun = new CloudRunServiceClient();
const cloudSQL = new CloudSQLAdminClient();
const redis = new CloudRedisClient();
const secretManager = new SecretManagerServiceClient();
const resourceManager = new ResourceManagerServiceClient();

// Create Infrastructure Resource Tool
const createInfrastructure: MCPTool = {
  name: 'create_infrastructure',
  description: 'Create any type of Google Cloud infrastructure resource',
  inputSchema: z.object({
    resourceType: ResourceTypeSchema,
    resourceName: z.string(),
    config: z.record(z.any()),
    region: z.string().optional(),
    labels: z.record(z.string()).optional()
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { resourceType, resourceName, config, region, labels } = args;
      const projectId = process.env.GOOGLE_CLOUD_PROJECT;
      
      let result;
      
      switch (resourceType) {
        case 'compute_instance':
          const [vmOperation] = await compute.zone(config.zone || 'us-central1-a').createVM(resourceName, {
            machineType: config.machineType || 'e2-medium',
            disks: [{
              boot: true,
              initializeParams: {
                sourceImage: config.sourceImage || 'projects/debian-cloud/global/images/family/debian-11'
              }
            }],
            networkInterfaces: [{
              network: 'global/networks/default'
            }],
            labels
          });
          result = { operation: vmOperation.name, resourceType, resourceName };
          break;
          
        case 'cloud_run_service':
          const [runService] = await cloudRun.createService({
            parent: `projects/${projectId}/locations/${region || 'us-central1'}`,
            service: {
              metadata: {
                name: resourceName,
                labels
              },
              spec: {
                template: {
                  spec: {
                    containers: [{
                      image: config.image,
                      resources: {
                        limits: {
                          cpu: config.cpu || '1',
                          memory: config.memory || '512Mi'
                        }
                      }
                    }]
                  }
                }
              }
            }
          });
          result = { service: runService.name, resourceType, resourceName };
          break;
          
        case 'storage_bucket':
          const [bucket] = await storage.createBucket(resourceName, {
            location: region || 'US',
            storageClass: config.storageClass || 'STANDARD',
            labels
          });
          result = { bucket: bucket.name, resourceType, resourceName };
          break;
          
        case 'cloud_sql':
          const [sqlOperation] = await cloudSQL.createInstance({
            project: projectId,
            instance: {
              name: resourceName,
              databaseVersion: config.databaseVersion || 'POSTGRES_15',
              region: region || 'us-central1',
              settings: {
                tier: config.tier || 'db-f1-micro',
                backupConfiguration: {
                  enabled: true,
                  startTime: '03:00'
                }
              },
              userLabels: labels
            }
          });
          result = { operation: sqlOperation.name, resourceType, resourceName };
          break;
          
        default:
          throw new Error(`Unsupported resource type: ${resourceType}`);
      }
      
      return {
        success: true,
        data: result,
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

// Delete Infrastructure Resource Tool
const deleteInfrastructure: MCPTool = {
  name: 'delete_infrastructure',
  description: 'Delete a Google Cloud infrastructure resource',
  inputSchema: z.object({
    resourceType: ResourceTypeSchema,
    resourceName: z.string(),
    region: z.string().optional(),
    force: z.boolean().optional()
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { resourceType, resourceName, region } = args;
      const projectId = process.env.GOOGLE_CLOUD_PROJECT;
      
      let result;
      
      switch (resourceType) {
        case 'compute_instance':
          const [vmDeleteOp] = await compute.zone(region || 'us-central1-a').vm(resourceName).delete();
          result = { operation: vmDeleteOp.name, resourceType, resourceName };
          break;
          
        case 'cloud_run_service':
          await cloudRun.deleteService({
            name: `projects/${projectId}/locations/${region || 'us-central1'}/services/${resourceName}`
          });
          result = { deleted: true, resourceType, resourceName };
          break;
          
        case 'storage_bucket':
          await storage.bucket(resourceName).delete();
          result = { deleted: true, resourceType, resourceName };
          break;
          
        default:
          throw new Error(`Unsupported resource type: ${resourceType}`);
      }
      
      return {
        success: true,
        data: result,
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

// List Infrastructure Resources Tool
const listInfrastructure: MCPTool = {
  name: 'list_infrastructure',
  description: 'List Google Cloud infrastructure resources',
  inputSchema: z.object({
    resourceType: ResourceTypeSchema,
    region: z.string().optional(),
    filters: z.record(z.string()).optional()
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { resourceType, region } = args;
      const projectId = process.env.GOOGLE_CLOUD_PROJECT;
      
      let resources;
      
      switch (resourceType) {
        case 'compute_instance':
          const [vms] = await compute.getVMs();
          resources = vms.map(vm => ({
            name: vm.name,
            status: vm.metadata?.status,
            zone: vm.zone?.split('/').pop(),
            machineType: vm.metadata?.machineType?.split('/').pop()
          }));
          break;
          
        case 'cloud_run_service':
          const [services] = await cloudRun.listServices({
            parent: `projects/${projectId}/locations/${region || '-'}`
          });
          resources = services.map(service => ({
            name: service.metadata?.name,
            url: service.status?.url,
            region: service.metadata?.labels?.['cloud.googleapis.com/location']
          }));
          break;
          
        case 'storage_bucket':
          const [buckets] = await storage.getBuckets();
          resources = buckets.map(bucket => ({
            name: bucket.name,
            location: bucket.metadata?.location,
            storageClass: bucket.metadata?.storageClass
          }));
          break;
          
        default:
          throw new Error(`Unsupported resource type: ${resourceType}`);
      }
      
      return {
        success: true,
        data: resources,
        metadata: {
          count: resources.length,
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

// Scale Infrastructure Resource Tool
const scaleInfrastructure: MCPTool = {
  name: 'scale_infrastructure',
  description: 'Scale Google Cloud infrastructure resources',
  inputSchema: z.object({
    resourceType: ResourceTypeSchema,
    resourceName: z.string(),
    scalingConfig: z.object({
      minInstances: z.number().optional(),
      maxInstances: z.number().optional(),
      targetCpuUtilization: z.number().optional(),
      targetMemoryUtilization: z.number().optional()
    }),
    region: z.string().optional()
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { resourceType, resourceName, scalingConfig, region } = args;
      const projectId = process.env.GOOGLE_CLOUD_PROJECT;
      
      let result;
      
      switch (resourceType) {
        case 'cloud_run_service':
          const [updatedService] = await cloudRun.updateService({
            service: {
              metadata: {
                name: `projects/${projectId}/locations/${region || 'us-central1'}/services/${resourceName}`
              },
              spec: {
                template: {
                  metadata: {
                    annotations: {
                      'autoscaling.knative.dev/minScale': String(scalingConfig.minInstances || 0),
                      'autoscaling.knative.dev/maxScale': String(scalingConfig.maxInstances || 100)
                    }
                  }
                }
              }
            }
          });
          result = { service: updatedService.name, scalingConfig };
          break;
          
        case 'gke_cluster':
          // Implement GKE autoscaling
          result = { cluster: resourceName, scalingConfig };
          break;
          
        default:
          throw new Error(`Scaling not supported for resource type: ${resourceType}`);
      }
      
      return {
        success: true,
        data: result,
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

export const infrastructureTools: MCPTool[] = [
  createInfrastructure,
  deleteInfrastructure,
  listInfrastructure,
  scaleInfrastructure
];

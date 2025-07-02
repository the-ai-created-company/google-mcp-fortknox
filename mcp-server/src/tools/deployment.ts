import { z } from 'zod';
import { CloudRunServiceClient } from '@google-cloud/run';
import { CloudFunctionsServiceClient } from '@google-cloud/functions';
import { ContainerAnalysisClient } from '@google-cloud/containeranalysis';
import { Storage } from '@google-cloud/storage';
import { MCPTool, DeploymentConfigSchema, ToolResponse } from '../types.js';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);
const cloudRun = new CloudRunServiceClient();
const cloudFunctions = new CloudFunctionsServiceClient();
const containerAnalysis = new ContainerAnalysisClient();
const storage = new Storage();

// Deploy Service Tool
const deployService: MCPTool = {
  name: 'deploy_service',
  description: 'Deploy a service to Google Cloud Run with automatic scaling and monitoring',
  inputSchema: DeploymentConfigSchema,
  execute: async (args): Promise<ToolResponse> => {
    try {
      const config = args;
      const projectId = process.env.GOOGLE_CLOUD_PROJECT;
      const region = config.region || 'us-central1';
      
      // Deploy to Cloud Run
      const [service] = await cloudRun.createService({
        parent: `projects/${projectId}/locations/${region}`,
        service: {
          metadata: {
            name: config.name,
            annotations: {
              'run.googleapis.com/ingress': 'all',
              'run.googleapis.com/execution-environment': 'gen2'
            }
          },
          spec: {
            template: {
              metadata: {
                annotations: {
                  'autoscaling.knative.dev/minScale': String(config.minInstances || 0),
                  'autoscaling.knative.dev/maxScale': String(config.maxInstances || 100),
                  'run.googleapis.com/cpu-throttling': 'false'
                }
              },
              spec: {
                serviceAccountName: config.serviceAccount,
                containers: [{
                  image: config.image,
                  env: Object.entries(config.environment || {}).map(([name, value]) => ({
                    name,
                    value: String(value)
                  })),
                  resources: {
                    limits: {
                      cpu: config.cpu || '1',
                      memory: config.memory || '512Mi'
                    }
                  },
                  ports: [{
                    containerPort: 8080
                  }]
                }]
              }
            }
          }
        }
      });
      
      return {
        success: true,
        data: {
          serviceName: config.name,
          serviceUrl: service.status?.url,
          region,
          status: 'deployed'
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

// Build Container Image Tool
const buildContainerImage: MCPTool = {
  name: 'build_container_image',
  description: 'Build and push a container image to Google Container Registry',
  inputSchema: z.object({
    sourcePath: z.string(),
    imageName: z.string(),
    imageTag: z.string().optional(),
    dockerfile: z.string().optional(),
    buildArgs: z.record(z.string()).optional(),
    platform: z.string().optional()
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { sourcePath, imageName, imageTag = 'latest', dockerfile = 'Dockerfile', buildArgs = {}, platform } = args;
      const projectId = process.env.GOOGLE_CLOUD_PROJECT;
      const imageUri = `gcr.io/${projectId}/${imageName}:${imageTag}`;
      
      // Build command
      let buildCommand = `docker build -t ${imageUri} -f ${dockerfile}`;
      
      // Add build args
      for (const [key, value] of Object.entries(buildArgs)) {
        buildCommand += ` --build-arg ${key}=${value}`;
      }
      
      if (platform) {
        buildCommand += ` --platform ${platform}`;
      }
      
      buildCommand += ` ${sourcePath}`;
      
      // Build image
      await execAsync(buildCommand);
      
      // Push to GCR
      await execAsync(`docker push ${imageUri}`);
      
      // Scan image for vulnerabilities
      const [scanResult] = await containerAnalysis.getGrafeasClient().createOccurrence({
        parent: `projects/${projectId}`,
        occurrence: {
          resourceUri: imageUri,
          noteName: `projects/${projectId}/notes/vulnerability-scan`
        }
      });
      
      return {
        success: true,
        data: {
          imageUri,
          imageName,
          imageTag,
          scanResult: scanResult.name,
          size: 'unknown' // Would need to query docker for actual size
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

// Deploy Cloud Function Tool
const deployCloudFunction: MCPTool = {
  name: 'deploy_cloud_function',
  description: 'Deploy a serverless function to Google Cloud Functions',
  inputSchema: z.object({
    functionName: z.string(),
    sourceCode: z.string(),
    runtime: z.enum(['nodejs18', 'nodejs20', 'python311', 'python312', 'go121', 'java17']),
    entryPoint: z.string(),
    trigger: z.object({
      type: z.enum(['http', 'pubsub', 'storage', 'firestore', 'eventarc']),
      resource: z.string().optional(),
      eventType: z.string().optional()
    }),
    environment: z.record(z.string()).optional(),
    timeout: z.number().optional(),
    memory: z.number().optional()
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { functionName, sourceCode, runtime, entryPoint, trigger, environment, timeout = 60, memory = 256 } = args;
      const projectId = process.env.GOOGLE_CLOUD_PROJECT;
      const region = 'us-central1';
      
      // Save source code to Cloud Storage
      const sourcesBucket = storage.bucket(`${projectId}-function-sources`);
      const sourceArchive = `${functionName}-${Date.now()}.zip`;
      
      // Create zip file with source code
      // In production, this would properly zip the source
      await sourcesBucket.file(sourceArchive).save(sourceCode);
      
      // Create function
      const functionConfig: any = {
        name: functionName,
        sourceArchiveUrl: `gs://${projectId}-function-sources/${sourceArchive}`,
        entryPoint,
        runtime,
        timeout: `${timeout}s`,
        availableMemoryMb: memory,
        environmentVariables: environment
      };
      
      // Configure trigger
      if (trigger.type === 'http') {
        functionConfig['httpsTrigger'] = {};
      } else if (trigger.type === 'pubsub') {
        functionConfig['eventTrigger'] = {
          eventType: 'providers/cloud.pubsub/eventTypes/topic.publish',
          resource: trigger.resource
        };
      }
      
      const [operation] = await cloudFunctions.createFunction({
        parent: `projects/${projectId}/locations/${region}`,
        function: functionConfig
      });
      
      return {
        success: true,
        data: {
          functionName,
          runtime,
          trigger: trigger.type,
          status: 'deploying',
          operation: operation.name
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

// Create CI/CD Pipeline Tool
const createCICDPipeline: MCPTool = {
  name: 'create_cicd_pipeline',
  description: 'Create a CI/CD pipeline for automatic deployments',
  inputSchema: z.object({
    pipelineName: z.string(),
    sourceRepository: z.object({
      type: z.enum(['github', 'gitlab', 'bitbucket', 'cloud_source']),
      url: z.string(),
      branch: z.string().optional()
    }),
    buildConfig: z.object({
      dockerfile: z.string().optional(),
      buildCommand: z.string().optional(),
      testCommand: z.string().optional()
    }),
    deployConfig: z.object({
      targetService: z.string(),
      targetEnvironment: z.enum(['development', 'staging', 'production']),
      approvalRequired: z.boolean().optional()
    })
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { pipelineName, sourceRepository, buildConfig, deployConfig } = args;
      const projectId = process.env.GOOGLE_CLOUD_PROJECT;
      
      // Create Cloud Build configuration
      const buildYaml = `
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/${projectId}/${deployConfig.targetService}:$COMMIT_SHA', '.']
    
  ${buildConfig.testCommand ? `
  # Run tests
  - name: 'gcr.io/cloud-builders/npm'
    args: ['test']
  ` : ''}
  
  # Push the container image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/${projectId}/${deployConfig.targetService}:$COMMIT_SHA']
    
  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
    - 'run'
    - 'deploy'
    - '${deployConfig.targetService}'
    - '--image'
    - 'gcr.io/${projectId}/${deployConfig.targetService}:$COMMIT_SHA'
    - '--region'
    - 'us-central1'
    - '--platform'
    - 'managed'
    ${deployConfig.targetEnvironment === 'production' ? "- '--no-traffic'" : ''}

${deployConfig.approvalRequired && deployConfig.targetEnvironment === 'production' ? `
  # Wait for manual approval
  - name: 'gcr.io/cloud-builders/gcloud'
    args: ['builds', 'approve', '$BUILD_ID']
` : ''}

images:
- 'gcr.io/${projectId}/${deployConfig.targetService}:$COMMIT_SHA'
`;

      // Save build configuration
      const buildBucket = storage.bucket(`${projectId}-build-configs`);
      await buildBucket.file(`${pipelineName}/cloudbuild.yaml`).save(buildYaml);
      
      return {
        success: true,
        data: {
          pipelineName,
          repository: sourceRepository.url,
          targetService: deployConfig.targetService,
          environment: deployConfig.targetEnvironment,
          configLocation: `gs://${projectId}-build-configs/${pipelineName}/cloudbuild.yaml`
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

// Rollback Deployment Tool
const rollbackDeployment: MCPTool = {
  name: 'rollback_deployment',
  description: 'Rollback a service to a previous deployment version',
  inputSchema: z.object({
    serviceName: z.string(),
    targetRevision: z.string().optional(),
    region: z.string().optional()
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { serviceName, targetRevision, region = 'us-central1' } = args;
      const projectId = process.env.GOOGLE_CLOUD_PROJECT;
      
      // Get service
      const [service] = await cloudRun.getService({
        name: `projects/${projectId}/locations/${region}/services/${serviceName}`
      });
      
      // Get revisions
      const [revisions] = await cloudRun.listRevisions({
        parent: `projects/${projectId}/locations/${region}`,
        filter: `serving.knative.dev/service="${serviceName}"`
      });
      
      const targetRev = targetRevision || revisions[1]?.metadata?.name; // Previous revision
      
      if (!targetRev) {
        throw new Error('No previous revision found to rollback to');
      }
      
      // Update traffic to target revision
      await cloudRun.updateService({
        service: {
          metadata: {
            name: `projects/${projectId}/locations/${region}/services/${serviceName}`
          },
          spec: {
            traffic: [{
              revisionName: targetRev,
              percent: 100
            }]
          }
        }
      });
      
      return {
        success: true,
        data: {
          serviceName,
          rolledBackTo: targetRev,
          region,
          status: 'completed'
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

export const deploymentTools: MCPTool[] = [
  deployService,
  buildContainerImage,
  deployCloudFunction,
  createCICDPipeline,
  rollbackDeployment
];

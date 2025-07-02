import { z } from 'zod';
import { CloudSQLAdminClient } from '@google-cloud/sql';
import { CloudRedisClient } from '@google-cloud/redis';
import { Firestore } from '@google-cloud/firestore';
import { BigQuery } from '@google-cloud/bigquery';
import { MCPTool, DatabaseConfigSchema, ToolResponse } from '../types.js';

const cloudSQL = new CloudSQLAdminClient();
const redis = new CloudRedisClient();
const firestore = new Firestore();
const bigquery = new BigQuery();

// Create Database Tool
const createDatabase: MCPTool = {
  name: 'create_database',
  description: 'Create a new database instance (Cloud SQL, Redis, Firestore, or BigQuery)',
  inputSchema: DatabaseConfigSchema,
  execute: async (args): Promise<ToolResponse> => {
    try {
      const config = args;
      const projectId = process.env.GOOGLE_CLOUD_PROJECT;
      const region = config.region || 'us-central1';
      
      let result;
      
      switch (config.type) {
        case 'postgres':
        case 'mysql':
          const [sqlOperation] = await cloudSQL.createInstance({
            project: projectId,
            instance: {
              name: config.name,
              databaseVersion: config.type === 'postgres' ? 'POSTGRES_15' : 'MYSQL_8_0',
              region,
              settings: {
                tier: config.tier || 'db-f1-micro',
                backupConfiguration: {
                  enabled: config.backups !== false,
                  startTime: '03:00',
                  pointInTimeRecoveryEnabled: true,
                  transactionLogRetentionDays: 7
                },
                ipConfiguration: {
                  ipv4Enabled: true,
                  authorizedNetworks: [],
                  requireSsl: true
                },
                availabilityType: config.highAvailability ? 'REGIONAL' : 'ZONAL'
              }
            }
          });
          
          result = {
            operation: sqlOperation.name,
            instanceName: config.name,
            type: config.type,
            connectionString: `postgresql://user:password@${config.name}:5432/database`
          };
          break;
          
        case 'redis':
          const [redisOperation] = await redis.createInstance({
            parent: `projects/${projectId}/locations/${region}`,
            instanceId: config.name,
            instance: {
              tier: config.tier || 'BASIC',
              memorySizeGb: 1,
              redisVersion: 'REDIS_7_0',
              authEnabled: true,
              transitEncryptionMode: 'SERVER_AUTHENTICATION',
              persistenceConfig: {
                persistenceMode: 'RDB',
                rdbSnapshotPeriod: 'ONE_HOUR'
              }
            }
          });
          
          result = {
            operation: redisOperation.name,
            instanceName: config.name,
            type: 'redis'
          };
          break;
          
        case 'firestore':
          // Firestore is automatically created with the project
          // Create collections and set security rules
          const db = firestore;
          const collectionName = `${config.name}_collection`;
          await db.collection(collectionName).doc('_init').set({
            created: new Date(),
            description: 'Initial document'
          });
          
          result = {
            database: 'firestore',
            collection: collectionName,
            type: 'firestore'
          };
          break;
          
        case 'bigquery':
          const [dataset] = await bigquery.createDataset(config.name, {
            location: region
          });
          
          result = {
            dataset: dataset.id,
            type: 'bigquery',
            location: region
          };
          break;
          
        default:
          throw new Error(`Unsupported database type: ${config.type}`);
      }
      
      // Set up permissions if specified
      if (config.permissions) {
        // TODO: Implement IAM permissions
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

// Execute Database Query Tool
const executeDatabaseQuery: MCPTool = {
  name: 'execute_database_query',
  description: 'Execute a query against a database',
  inputSchema: z.object({
    databaseName: z.string(),
    databaseType: z.enum(['postgres', 'mysql', 'bigquery', 'firestore']),
    query: z.string(),
    parameters: z.record(z.any()).optional()
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { databaseName, databaseType, query, parameters } = args;
      const projectId = process.env.GOOGLE_CLOUD_PROJECT;
      
      let result;
      
      switch (databaseType) {
        case 'bigquery':
          const [job] = await bigquery.createQueryJob({
            query,
            params: parameters,
            location: 'US'
          });
          const [rows] = await job.getQueryResults();
          result = { rows, rowCount: rows.length };
          break;
          
        case 'firestore':
          // Parse Firestore query syntax
          const parts = query.split(' ');
          const collection = parts[0];
          const operation = parts[1];
          
          if (operation === 'SELECT') {
            const snapshot = await firestore.collection(collection).get();
            result = {
              documents: snapshot.docs.map(doc => ({
                id: doc.id,
                data: doc.data()
              })),
              count: snapshot.size
            };
          } else if (operation === 'INSERT') {
            const doc = await firestore.collection(collection).add(parameters || {});
            result = { id: doc.id, created: true };
          }
          break;
          
        default:
          throw new Error(`Query execution not implemented for ${databaseType}`);
      }
      
      return {
        success: true,
        data: result,
        metadata: {
          databaseName,
          databaseType,
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

// Create Database Schema Tool
const createDatabaseSchema: MCPTool = {
  name: 'create_database_schema',
  description: 'Create or update database schema (tables, collections, etc.)',
  inputSchema: z.object({
    databaseName: z.string(),
    databaseType: z.enum(['postgres', 'mysql', 'bigquery', 'firestore']),
    schema: z.object({
      tables: z.array(z.object({
        name: z.string(),
        columns: z.array(z.object({
          name: z.string(),
          type: z.string(),
          nullable: z.boolean().optional(),
          primaryKey: z.boolean().optional(),
          unique: z.boolean().optional()
        }))
      })).optional(),
      collections: z.array(z.object({
        name: z.string(),
        indexes: z.array(z.object({
          fields: z.array(z.string()),
          unique: z.boolean().optional()
        })).optional()
      })).optional()
    })
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { databaseName, databaseType, schema } = args;
      const projectId = process.env.GOOGLE_CLOUD_PROJECT;
      
      let result;
      
      switch (databaseType) {
        case 'bigquery':
          if (schema.tables) {
            for (const table of schema.tables) {
              const tableSchema = table.columns.map(col => ({
                name: col.name,
                type: col.type,
                mode: col.nullable ? 'NULLABLE' : 'REQUIRED'
              }));
              
              await bigquery
                .dataset(databaseName)
                .createTable(table.name, { schema: tableSchema });
            }
            result = { tables: schema.tables.map(t => t.name) };
          }
          break;
          
        case 'firestore':
          if (schema.collections) {
            for (const collection of schema.collections) {
              // Create collection with initial document
              await firestore.collection(collection.name).doc('_schema').set({
                created: new Date(),
                indexes: collection.indexes || []
              });
              
              // Note: Firestore indexes need to be created via Firebase Console or CLI
            }
            result = { collections: schema.collections.map(c => c.name) };
          }
          break;
          
        default:
          throw new Error(`Schema creation not implemented for ${databaseType}`);
      }
      
      return {
        success: true,
        data: result,
        metadata: {
          databaseName,
          databaseType,
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

// Backup Database Tool
const backupDatabase: MCPTool = {
  name: 'backup_database',
  description: 'Create a backup of a database',
  inputSchema: z.object({
    databaseName: z.string(),
    databaseType: z.enum(['postgres', 'mysql', 'redis', 'firestore', 'bigquery']),
    backupName: z.string().optional(),
    exportLocation: z.string().optional()
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { databaseName, databaseType, backupName, exportLocation } = args;
      const projectId = process.env.GOOGLE_CLOUD_PROJECT;
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const backupId = backupName || `backup-${databaseName}-${timestamp}`;
      
      let result;
      
      switch (databaseType) {
        case 'postgres':
        case 'mysql':
          const [backupOperation] = await cloudSQL.createBackup({
            project: projectId,
            backup: {
              name: backupId,
              instance: databaseName,
              description: `Backup created by MCP tool at ${timestamp}`
            }
          });
          
          result = {
            operation: backupOperation.name,
            backupId,
            status: 'initiated'
          };
          break;
          
        case 'firestore':
          // Firestore export to Cloud Storage
          const exportPath = exportLocation || `gs://instabids-backups/firestore/${backupId}`;
          // Note: Firestore export requires additional setup
          result = {
            exportPath,
            backupId,
            status: 'export_configured'
          };
          break;
          
        case 'bigquery':
          if (exportLocation) {
            const dataset = bigquery.dataset(databaseName);
            const [tables] = await dataset.getTables();
            
            for (const table of tables) {
              await table.extract(`${exportLocation}/${table.id}/*.json`);
            }
            
            result = {
              exportPath: exportLocation,
              tablesExported: tables.length,
              backupId
            };
          }
          break;
          
        default:
          throw new Error(`Backup not implemented for ${databaseType}`);
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

// List Databases Tool
const listDatabases: MCPTool = {
  name: 'list_databases',
  description: 'List all databases in the project',
  inputSchema: z.object({
    databaseType: z.enum(['all', 'postgres', 'mysql', 'redis', 'firestore', 'bigquery']).optional()
  }),
  execute: async (args): Promise<ToolResponse> => {
    try {
      const { databaseType = 'all' } = args;
      const projectId = process.env.GOOGLE_CLOUD_PROJECT;
      const databases = [];
      
      if (databaseType === 'all' || databaseType === 'postgres' || databaseType === 'mysql') {
        const [instances] = await cloudSQL.listInstances({
          project: projectId
        });
        
        databases.push(...instances.map(instance => ({
          name: instance.name,
          type: instance.databaseVersion?.startsWith('POSTGRES') ? 'postgres' : 'mysql',
          region: instance.region,
          tier: instance.settings?.tier,
          status: instance.state
        })));
      }
      
      if (databaseType === 'all' || databaseType === 'redis') {
        const [redisInstances] = await redis.listInstances({
          parent: `projects/${projectId}/locations/-`
        });
        
        databases.push(...redisInstances.map(instance => ({
          name: instance.name?.split('/').pop(),
          type: 'redis',
          region: instance.locationId,
          tier: instance.tier,
          status: instance.state
        })));
      }
      
      if (databaseType === 'all' || databaseType === 'bigquery') {
        const [datasets] = await bigquery.getDatasets();
        
        databases.push(...datasets.map(dataset => ({
          name: dataset.id,
          type: 'bigquery',
          region: dataset.metadata?.location,
          status: 'active'
        })));
      }
      
      return {
        success: true,
        data: databases,
        metadata: {
          count: databases.length,
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

export const databaseTools: MCPTool[] = [
  createDatabase,
  executeDatabaseQuery,
  createDatabaseSchema,
  backupDatabase,
  listDatabases
];

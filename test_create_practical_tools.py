#!/usr/bin/env python
"""Test creating a practical Google Cloud MCP tool"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from agents.base_agent import BaseAgent
    print("[OK] Successfully imported BaseAgent")
    
    # Create a test agent
    agent = BaseAgent(
        agent_id="test-creator-002",
        name="CloudToolCreator",
        capabilities=["tool-creation", "google-cloud"]
    )
    print(f"[OK] Created agent: {agent.name}")
    
    # Create a practical Google Cloud Storage MCP tool
    tool_code = '''import { z } from 'zod';
import { Storage } from '@google-cloud/storage';

export const listBucketsTool = {
  name: 'gcs_list_buckets',
  description: 'List all Google Cloud Storage buckets in the current project',
  schema: z.object({
    projectId: z.string().describe('Google Cloud Project ID'),
    limit: z.number().optional().default(10).describe('Maximum number of buckets to return')
  }),
  execute: async ({ projectId, limit }) => {
    try {
      const storage = new Storage({ projectId });
      const [buckets] = await storage.getBuckets();
      
      const bucketList = buckets.slice(0, limit).map(bucket => ({
        name: bucket.name,
        created: bucket.metadata.timeCreated,
        location: bucket.metadata.location,
        storageClass: bucket.metadata.storageClass
      }));
      
      return {
        success: true,
        count: bucketList.length,
        total: buckets.length,
        buckets: bucketList,
        message: `Found ${buckets.length} buckets in project ${projectId}`
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        hint: 'Make sure you have proper Google Cloud credentials configured'
      };
    }
  }
};

export const createBucketTool = {
  name: 'gcs_create_bucket',
  description: 'Create a new Google Cloud Storage bucket',
  schema: z.object({
    projectId: z.string().describe('Google Cloud Project ID'),
    bucketName: z.string().describe('Name for the new bucket (must be globally unique)'),
    location: z.string().optional().default('US').describe('Bucket location'),
    storageClass: z.string().optional().default('STANDARD').describe('Storage class')
  }),
  execute: async ({ projectId, bucketName, location, storageClass }) => {
    try {
      const storage = new Storage({ projectId });
      const [bucket] = await storage.createBucket(bucketName, {
        location,
        storageClass
      });
      
      return {
        success: true,
        bucket: {
          name: bucket.name,
          created: bucket.metadata.timeCreated,
          location: bucket.metadata.location,
          storageClass: bucket.metadata.storageClass
        },
        message: `Successfully created bucket ${bucketName}`
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        hint: error.code === 409 ? 'Bucket name already exists. Try a different name.' : 'Check your permissions and project settings'
      };
    }
  }
};
'''
    
    print("\n[ACTION] Creating practical GCS MCP tools...")
    result = agent.create_mcp_tool(
        tool_name="gcs_operations",
        tool_code=tool_code,
        category="google-cloud"
    )
    print(f"[OK] Tool creation result: {result}")
    
    # Create another tool for Compute Engine
    compute_tool_code = '''import { z } from 'zod';
import { Compute } from '@google-cloud/compute';

export const listInstancesTool = {
  name: 'compute_list_instances',
  description: 'List all Compute Engine instances in a project',
  schema: z.object({
    projectId: z.string().describe('Google Cloud Project ID'),
    zone: z.string().optional().describe('Specific zone to query (leave empty for all zones)')
  }),
  execute: async ({ projectId, zone }) => {
    try {
      const compute = new Compute({ projectId });
      let instances = [];
      
      if (zone) {
        const [vms] = await compute.zone(zone).getVMs();
        instances = vms;
      } else {
        const [vms] = await compute.getVMs();
        instances = vms;
      }
      
      const instanceList = instances.map(vm => ({
        name: vm.name,
        zone: vm.zone.name,
        machineType: vm.metadata.machineType.split('/').pop(),
        status: vm.metadata.status,
        externalIP: vm.metadata.networkInterfaces?.[0]?.accessConfigs?.[0]?.natIP || 'None',
        internalIP: vm.metadata.networkInterfaces?.[0]?.networkIP || 'None'
      }));
      
      return {
        success: true,
        count: instanceList.length,
        instances: instanceList,
        message: `Found ${instanceList.length} instances`
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }
};
'''
    
    result2 = agent.create_mcp_tool(
        tool_name="compute_operations",
        tool_code=compute_tool_code,
        category="google-cloud"
    )
    print(f"[OK] Second tool creation result: {result2}")
    
    # Check the tool registry
    print("\n[ACTION] Checking tool registry...")
    registry_path = agent.mcp_tools_path / "tool_registry.json"
    if registry_path.exists():
        import json
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        print(f"[OK] Tool registry now contains: {json.dumps(registry, indent=2)}")
    
    print("\n[SUCCESS] Created practical MCP tools that could be used in production!")
    
except Exception as e:
    print(f"[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()

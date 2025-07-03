"""Tool Creator Agent

This agent specializes in creating MCP tools by:
- Analyzing Fort Knox API documentation
- Generating tool implementations
- Testing tool functionality
- Deploying tools for other agents to use
- Creating documentation for new tools
"""

from pathlib import Path
import sys
import json
import re

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base_agent import BaseAgent
from typing import Dict, List, Any, Optional


class ToolCreatorAgent(BaseAgent):
    """Agent specialized in creating MCP tools from API documentation"""
    
    def __init__(self):
        super().__init__(
            agent_id="agent-02-tool-creator",
            name="Tool Creator",
            capabilities=[
                "analyze_api_docs",
                "generate_tool_code",
                "create_mcp_tools",
                "test_tools",
                "document_tools",
                "optimize_tool_performance",
                "create_tool_chains"
            ]
        )
        self.created_tools = []
        self.tool_templates = self._load_tool_templates()
    
    def _load_tool_templates(self) -> Dict[str, str]:
        """Load templates for different tool types"""
        return {
            "basic": self._get_basic_template(),
            "crud": self._get_crud_template(),
            "batch": self._get_batch_template(),
            "streaming": self._get_streaming_template()
        }
    
    def _get_basic_template(self) -> str:
        """Get basic tool template"""
        return """import { Tool } from '@modelcontextprotocol/sdk';
import { z } from 'zod';

export const {tool_name}: Tool = {
  name: '{tool_name}',
  description: '{description}',
  inputSchema: {schema},
  
  async execute(params: z.infer<typeof inputSchema>) {
    try {
      // Implementation here
      {implementation}
      
      return {
        success: true,
        data: result,
        message: '{tool_name} executed successfully'
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        details: error
      };
    }
  }
};
"""
    
    def _get_crud_template(self) -> str:
        """Get CRUD operations template"""
        return """import { Tool } from '@modelcontextprotocol/sdk';
import { z } from 'zod';
import { google } from 'googleapis';

// CRUD Tool for {resource_name}
export class {resource_name}CRUDTools {
  private auth: any;
  
  constructor() {
    this.auth = new google.auth.GoogleAuth({
      scopes: ['https://www.googleapis.com/auth/cloud-platform']
    });
  }
  
  create: Tool = {
    name: 'create_{resource_name_lower}',
    description: 'Create a new {resource_name}',
    inputSchema: {create_schema},
    async execute(params) {
      const client = await this.auth.getClient();
      const response = await client.request({
        method: 'POST',
        url: '{create_url}',
        data: params
      });
      return { success: true, data: response.data };
    }
  };
  
  read: Tool = {
    name: 'get_{resource_name_lower}',
    description: 'Get a {resource_name}',
    inputSchema: {read_schema},
    async execute(params) {
      const client = await this.auth.getClient();
      const response = await client.request({
        method: 'GET',
        url: '{read_url}'
      });
      return { success: true, data: response.data };
    }
  };
  
  update: Tool = {
    name: 'update_{resource_name_lower}',
    description: 'Update a {resource_name}',
    inputSchema: {update_schema},
    async execute(params) {
      const client = await this.auth.getClient();
      const response = await client.request({
        method: 'PATCH',
        url: '{update_url}',
        data: params
      });
      return { success: true, data: response.data };
    }
  };
  
  delete: Tool = {
    name: 'delete_{resource_name_lower}',
    description: 'Delete a {resource_name}',
    inputSchema: {delete_schema},
    async execute(params) {
      const client = await this.auth.getClient();
      const response = await client.request({
        method: 'DELETE',
        url: '{delete_url}'
      });
      return { success: true, message: '{resource_name} deleted successfully' };
    }
  };
  
  list: Tool = {
    name: 'list_{resource_name_lower}s',
    description: 'List all {resource_name}s',
    inputSchema: {list_schema},
    async execute(params) {
      const client = await this.auth.getClient();
      const response = await client.request({
        method: 'GET',
        url: '{list_url}',
        params: params
      });
      return { success: true, data: response.data };
    }
  };
}
"""
    
    def _get_batch_template(self) -> str:
        """Get batch operations template"""
        return """import { Tool } from '@modelcontextprotocol/sdk';
import { z } from 'zod';
import pLimit from 'p-limit';

export const {tool_name}_batch: Tool = {
  name: '{tool_name}_batch',
  description: 'Execute {tool_name} in batch with concurrency control',
  inputSchema: z.object({
    items: z.array({item_schema}),
    concurrency: z.number().min(1).max(10).default(5)
  }),
  
  async execute({ items, concurrency }) {
    const limit = pLimit(concurrency);
    const results = [];
    const errors = [];
    
    const promises = items.map((item, index) => 
      limit(async () => {
        try {
          const result = await {operation}(item);
          results.push({ index, success: true, data: result });
        } catch (error) {
          errors.push({ index, success: false, error: error.message });
        }
      })
    );
    
    await Promise.all(promises);
    
    return {
      success: errors.length === 0,
      total: items.length,
      successful: results.length,
      failed: errors.length,
      results,
      errors
    };
  }
};
"""
    
    def _get_streaming_template(self) -> str:
        """Get streaming operations template"""
        return """import { Tool } from '@modelcontextprotocol/sdk';
import { z } from 'zod';
import { Readable } from 'stream';

export const {tool_name}_stream: Tool = {
  name: '{tool_name}_stream',
  description: 'Stream {resource_name} data',
  inputSchema: {schema},
  
  async execute(params) {
    const stream = new Readable({
      async read() {
        // Streaming implementation
      }
    });
    
    return {
      success: true,
      stream: stream,
      message: 'Streaming {resource_name} data'
    };
  }
};
"""
    
    def analyze_api_for_tools(self, service: str) -> List[Dict[str, Any]]:
        """Analyze Fort Knox API docs to identify tool opportunities"""
        docs = self.read_fort_knox_docs(service)
        if not docs:
            return []
        
        tool_opportunities = []
        
        # Analyze endpoints
        endpoints = docs.get("api_endpoints", {})
        resources = docs.get("resource_types", {})
        
        # Find CRUD patterns
        crud_resources = self._identify_crud_patterns(endpoints, resources)
        for resource in crud_resources:
            tool_opportunities.append({
                "type": "crud",
                "resource": resource,
                "priority": "high",
                "estimated_complexity": "medium"
            })
        
        # Find batch operation opportunities
        batch_ops = self._identify_batch_opportunities(endpoints)
        for op in batch_ops:
            tool_opportunities.append({
                "type": "batch",
                "operation": op,
                "priority": "medium",
                "estimated_complexity": "medium"
            })
        
        # Find streaming opportunities
        streaming_ops = self._identify_streaming_opportunities(endpoints)
        for op in streaming_ops:
            tool_opportunities.append({
                "type": "streaming",
                "operation": op,
                "priority": "low",
                "estimated_complexity": "high"
            })
        
        return tool_opportunities
    
    def _identify_crud_patterns(self, endpoints: Dict, resources: Dict) -> List[str]:
        """Identify resources with CRUD operations"""
        crud_resources = []
        
        for resource_name, resource_ops in resources.items():
            operations = set(resource_ops.get("operations", []))
            crud_ops = {"create", "get", "update", "delete", "list"}
            
            # Check if resource has most CRUD operations
            if len(operations.intersection(crud_ops)) >= 3:
                crud_resources.append(resource_name)
        
        return crud_resources
    
    def _identify_batch_opportunities(self, endpoints: Dict) -> List[str]:
        """Identify operations that could benefit from batch processing"""
        batch_ops = []
        
        for endpoint_name, endpoint_data in endpoints.items():
            # Look for operations that typically need batching
            if any(keyword in endpoint_name.lower() for keyword in ["create", "update", "delete"]):
                if "list" not in endpoint_name.lower() and "batch" not in endpoint_name.lower():
                    batch_ops.append(endpoint_name)
        
        return batch_ops[:5]  # Limit to top 5
    
    def _identify_streaming_opportunities(self, endpoints: Dict) -> List[str]:
        """Identify operations that could benefit from streaming"""
        streaming_ops = []
        
        for endpoint_name, endpoint_data in endpoints.items():
            # Look for operations that typically involve large data
            if any(keyword in endpoint_name.lower() for keyword in ["list", "export", "download", "logs"]):
                streaming_ops.append(endpoint_name)
        
        return streaming_ops[:3]  # Limit to top 3
    
    def create_tool_from_endpoint(self, service: str, endpoint_name: str, template_type: str = "basic") -> str:
        """Create a tool from a specific endpoint"""
        docs = self.read_fort_knox_docs(service)
        if not docs:
            return f"No documentation found for service: {service}"
        
        endpoints = docs.get("api_endpoints", {})
        endpoint = endpoints.get(endpoint_name)
        
        if not endpoint:
            return f"Endpoint {endpoint_name} not found in {service}"
        
        # Generate tool code
        tool_code = self._generate_tool_from_template(
            template_type,
            service,
            endpoint_name,
            endpoint
        )
        
        # Create the tool
        tool_name = f"{service}_{endpoint_name.replace('.', '_')}"
        result = self.create_mcp_tool(tool_name, tool_code, service)
        
        # Track created tool
        self.created_tools.append({
            "name": tool_name,
            "service": service,
            "endpoint": endpoint_name,
            "template": template_type,
            "created_at": self._get_timestamp()
        })
        
        # Store in knowledge base
        self.store_knowledge(
            f"tool_{tool_name}",
            {
                "service": service,
                "endpoint": endpoint_name,
                "template": template_type,
                "created_by": self.agent_id
            },
            category="created_tools"
        )
        
        return result
    
    def _generate_tool_from_template(self, template_type: str, service: str, endpoint_name: str, endpoint: Dict) -> str:
        """Generate tool code from template"""
        template = self.tool_templates.get(template_type, self.tool_templates["basic"])
        
        # Extract endpoint details
        method = endpoint.get("method", "GET")
        path = endpoint.get("path", "")
        description = endpoint.get("description", "")
        parameters = endpoint.get("parameters", {})
        
        # Generate schema
        schema = self._generate_zod_schema(parameters)
        
        # Generate implementation
        implementation = self._generate_implementation(service, method, path, parameters)
        
        # Fill template
        tool_code = template.format(
            tool_name=endpoint_name.replace(".", "_"),
            description=description,
            schema=schema,
            implementation=implementation,
            resource_name=self._extract_resource_name(endpoint_name),
            resource_name_lower=self._extract_resource_name(endpoint_name).lower(),
            create_url=f"https://{service}.googleapis.com{path}",
            read_url=f"https://{service}.googleapis.com{path}/{{id}}",
            update_url=f"https://{service}.googleapis.com{path}/{{id}}",
            delete_url=f"https://{service}.googleapis.com{path}/{{id}}",
            list_url=f"https://{service}.googleapis.com{path}",
            create_schema=schema,
            read_schema="z.object({ id: z.string() })",
            update_schema=schema,
            delete_schema="z.object({ id: z.string() })",
            list_schema="z.object({ pageSize: z.number().optional(), pageToken: z.string().optional() })",
            item_schema=schema,
            operation=endpoint_name
        )
        
        return tool_code
    
    def _generate_zod_schema(self, parameters: Dict) -> str:
        """Generate Zod schema from parameters"""
        schema_parts = []
        
        for param_name, param_info in parameters.items():
            param_type = param_info.get("type", "string")
            required = param_info.get("required", False)
            description = param_info.get("description", "")
            
            # Map to Zod type
            zod_type = self._get_zod_type(param_type)
            
            # Build schema line
            schema_line = f"  {param_name}: {zod_type}"
            if description:
                schema_line += f'.describe("{description}")'
            if not required:
                schema_line += ".optional()"
            
            schema_parts.append(schema_line)
        
        return "z.object({\n" + ",\n".join(schema_parts) + "\n})"
    
    def _get_zod_type(self, json_type: str) -> str:
        """Map JSON type to Zod type"""
        type_map = {
            "string": "z.string()",
            "number": "z.number()",
            "integer": "z.number().int()",
            "boolean": "z.boolean()",
            "array": "z.array(z.any())",
            "object": "z.object({})"
        }
        return type_map.get(json_type, "z.any()")
    
    def _generate_implementation(self, service: str, method: str, path: str, parameters: Dict) -> str:
        """Generate implementation code"""
        impl_lines = [
            f"const auth = new google.auth.GoogleAuth({{",
            f"  scopes: ['https://www.googleapis.com/auth/cloud-platform']",
            f"}});",
            f"const client = await auth.getClient();",
            f"",
            f"const response = await client.request({{",
            f"  method: '{method}',",
            f"  url: `https://{service}.googleapis.com{path}`,",
        ]
        
        if method in ["POST", "PUT", "PATCH"]:
            impl_lines.append("  data: params,")
        elif parameters:
            impl_lines.append("  params: params,")
        
        impl_lines.extend([
            "});",
            "",
            "const result = response.data;"
        ])
        
        return "\n      ".join(impl_lines)
    
    def _extract_resource_name(self, endpoint_name: str) -> str:
        """Extract resource name from endpoint"""
        parts = endpoint_name.split(".")
        if len(parts) > 1:
            return parts[-2].title()
        return endpoint_name.replace("_", " ").title()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def create_tool_suite(self, service: str) -> Dict[str, Any]:
        """Create a complete suite of tools for a service"""
        opportunities = self.analyze_api_for_tools(service)
        created_tools = []
        failed_tools = []
        
        for opportunity in opportunities[:10]:  # Limit to 10 tools per run
            try:
                if opportunity["type"] == "crud":
                    result = self.create_crud_tools(service, opportunity["resource"])
                else:
                    # Find relevant endpoint
                    endpoint = self._find_endpoint_for_operation(service, opportunity.get("operation", ""))
                    if endpoint:
                        result = self.create_tool_from_endpoint(service, endpoint, opportunity["type"])
                    else:
                        result = f"No endpoint found for operation: {opportunity.get('operation', '')}"
                
                created_tools.append({
                    "type": opportunity["type"],
                    "result": result
                })
            except Exception as e:
                failed_tools.append({
                    "type": opportunity["type"],
                    "error": str(e)
                })
        
        return {
            "service": service,
            "total_opportunities": len(opportunities),
            "created": len(created_tools),
            "failed": len(failed_tools),
            "created_tools": created_tools,
            "failed_tools": failed_tools
        }
    
    def create_crud_tools(self, service: str, resource: str) -> str:
        """Create CRUD tools for a resource"""
        # Generate CRUD tool code
        tool_code = self._generate_tool_from_template("crud", service, resource, {})
        
        # Create the tool file
        tool_name = f"{service}_{resource}_crud"
        result = self.create_mcp_tool(tool_name, tool_code, service)
        
        return result
    
    def _find_endpoint_for_operation(self, service: str, operation: str) -> Optional[str]:
        """Find endpoint name for an operation"""
        docs = self.read_fort_knox_docs(service)
        if not docs:
            return None
        
        endpoints = docs.get("api_endpoints", {})
        
        # Simple matching - could be enhanced
        for endpoint_name in endpoints:
            if operation.lower() in endpoint_name.lower():
                return endpoint_name
        
        return None
    
    def process_message(self, message: str) -> str:
        """Process incoming messages about tool creation"""
        message_lower = message.lower()
        
        # Check if asking to analyze a service
        if "analyze" in message_lower:
            # Extract service name (simple implementation)
            services = self.list_available_services()
            for service in services:
                if service in message_lower:
                    opportunities = self.analyze_api_for_tools(service)
                    return f"Found {len(opportunities)} tool opportunities in {service}: {[op['type'] for op in opportunities[:5]]}"
        
        # Check if asking to create tools
        if "create" in message_lower and "tool" in message_lower:
            # Extract service
            services = self.list_available_services()
            for service in services:
                if service in message_lower:
                    if "suite" in message_lower or "all" in message_lower:
                        result = self.create_tool_suite(service)
                        return f"Created {result['created']} tools for {service}. Failed: {result['failed']}"
                    else:
                        # Create single tool - need more context
                        return f"Please specify which endpoint or operation you want a tool for in {service}"
        
        # Check if asking about created tools
        if "list" in message_lower and "created" in message_lower:
            return f"I have created {len(self.created_tools)} tools: {[t['name'] for t in self.created_tools[-5:]]}"
        
        return f"Tool Creator Agent ready. I can analyze APIs and create MCP tools. Message: {message}"
    
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool creation tasks"""
        task_type = task.get("type", "")
        
        if task_type == "analyze_service":
            service = task.get("service", "")
            opportunities = self.analyze_api_for_tools(service)
            return {"status": "completed", "result": opportunities}
        
        elif task_type == "create_tool":
            service = task.get("service", "")
            endpoint = task.get("endpoint", "")
            template = task.get("template", "basic")
            result = self.create_tool_from_endpoint(service, endpoint, template)
            return {"status": "completed", "result": result}
        
        elif task_type == "create_tool_suite":
            service = task.get("service", "")
            result = self.create_tool_suite(service)
            return {"status": "completed", "result": result}
        
        else:
            return {"status": "error", "result": f"Unknown task type: {task_type}"}


# Agent initialization
if __name__ == "__main__":
    agent = ToolCreatorAgent()
    print(f"Tool Creator Agent initialized: {agent.agent_id}")
    print(f"Capabilities: {agent.capabilities}")

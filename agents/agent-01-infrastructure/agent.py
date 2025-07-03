"""Infrastructure Management Agent

This agent specializes in managing Google Cloud infrastructure by:
- Reading Fort Knox documentation to understand available services
- Creating and configuring cloud resources
- Monitoring infrastructure health
- Scaling services based on demand
- Creating MCP tools for infrastructure automation
"""

from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import json


class InfrastructureAgent(BaseAgent):
    """Agent specialized in Google Cloud infrastructure management"""
    
    def __init__(self):
        super().__init__(
            agent_id="agent-01-infrastructure",
            name="Infrastructure Manager",
            capabilities=[
                "create_resources",
                "scale_services", 
                "monitor_health",
                "optimize_costs",
                "manage_networking",
                "configure_security",
                "automate_deployments"
            ]
        )
        self.supported_services = [
            "compute",
            "storage",
            "run",
            "sql",
            "memorystore",
            "bigquery",
            "pubsub",
            "vpc",
            "loadbalancing"
        ]
    
    def analyze_infrastructure_needs(self) -> Dict[str, Any]:
        """Analyze available Fort Knox docs to understand infrastructure options"""
        analysis = {
            "available_services": {},
            "recommended_tools": [],
            "missing_documentation": []
        }
        
        # Check which services have documentation
        for service in self.supported_services:
            docs = self.read_fort_knox_docs(service)
            if docs:
                analysis["available_services"][service] = {
                    "documented": True,
                    "endpoints": len(docs.get("api_endpoints", {})),
                    "resources": list(docs.get("resource_types", {}).keys()) if "resource_types" in docs else []
                }
            else:
                analysis["missing_documentation"].append(service)
        
        # Recommend tools to create based on available docs
        if "compute" in analysis["available_services"]:
            analysis["recommended_tools"].append({
                "name": "compute_instance_manager",
                "purpose": "Manage Compute Engine instances",
                "priority": "high"
            })
        
        if "storage" in analysis["available_services"]:
            analysis["recommended_tools"].append({
                "name": "storage_bucket_manager",
                "purpose": "Manage Cloud Storage buckets",
                "priority": "high"
            })
        
        return analysis
    
    def create_infrastructure_tool(self, service: str, operation: str) -> str:
        """Create an MCP tool for a specific infrastructure operation"""
        # Read the Fort Knox documentation for this service
        docs = self.read_fort_knox_docs(service)
        if not docs:
            return f"No documentation found for service: {service}"
        
        # Find the relevant endpoint
        endpoints = docs.get("api_endpoints", {})
        relevant_endpoint = None
        
        for endpoint_name, endpoint_data in endpoints.items():
            if operation.lower() in endpoint_name.lower():
                relevant_endpoint = endpoint_data
                break
        
        if not relevant_endpoint:
            return f"No endpoint found for operation: {operation} in service: {service}"
        
        # Generate MCP tool code
        tool_code = self._generate_tool_code(service, operation, relevant_endpoint)
        
        # Create the tool
        tool_name = f"{service}_{operation}_tool"
        result = self.create_mcp_tool(tool_name, tool_code, "infrastructure")
        
        # Store knowledge about the created tool
        self.store_knowledge(
            f"tool_{tool_name}",
            {
                "service": service,
                "operation": operation,
                "endpoint": relevant_endpoint.get("id", ""),
                "created_by": self.agent_id
            },
            category="infrastructure_tools"
        )
        
        return result
    
    def _generate_tool_code(self, service: str, operation: str, endpoint: Dict[str, Any]) -> str:
        """Generate TypeScript code for an MCP tool"""
        method = endpoint.get("method", "GET")
        path = endpoint.get("path", "")
        description = endpoint.get("description", "")
        parameters = endpoint.get("parameters", {})
        
        # Generate parameter interface
        param_interface = self._generate_param_interface(parameters)
        
        tool_code = f"""import {{ Tool }} from '@modelcontextprotocol/sdk';
import {{ google }} from 'googleapis';

// Auto-generated tool for {service} - {operation}
// Generated by Infrastructure Agent using Fort Knox documentation

interface {operation.title()}Params {{
{param_interface}
}}

export const {service}_{operation}_tool: Tool = {{
  name: '{service}_{operation}',
  description: '{description}',
  inputSchema: {{
    type: 'object',
    properties: {self._generate_schema_properties(parameters)},
    required: {json.dumps(self._get_required_params(parameters))}
  }},
  
  async execute(params: {operation.title()}Params) {{
    try {{
      // Initialize Google Cloud client
      const auth = new google.auth.GoogleAuth({{
        scopes: ['https://www.googleapis.com/auth/cloud-platform']
      }});
      
      const authClient = await auth.getClient();
      
      // Make API request
      const response = await authClient.request({{
        method: '{method}',
        url: `https://{service}.googleapis.com{path}`,
        params: params
      }});
      
      return {{
        success: true,
        data: response.data,
        message: '{operation} completed successfully'
      }};
      
    }} catch (error) {{
      return {{
        success: false,
        error: error.message,
        details: error.response?.data || error
      }};
    }}
  }}
}};
"""
        return tool_code
    
    def _generate_param_interface(self, parameters: Dict[str, Any]) -> str:
        """Generate TypeScript interface for parameters"""
        lines = []
        for param_name, param_info in parameters.items():
            param_type = self._get_typescript_type(param_info.get("type", "string"))
            required = param_info.get("required", False)
            optional = "" if required else "?"
            description = param_info.get("description", "")
            
            if description:
                lines.append(f"  /** {description} */")
            lines.append(f"  {param_name}{optional}: {param_type};")
        
        return "\n".join(lines)
    
    def _generate_schema_properties(self, parameters: Dict[str, Any]) -> str:
        """Generate JSON schema properties"""
        props = {}
        for param_name, param_info in parameters.items():
            props[param_name] = {
                "type": param_info.get("type", "string"),
                "description": param_info.get("description", "")
            }
        return json.dumps(props, indent=4).replace('\n', '\n      ')
    
    def _get_required_params(self, parameters: Dict[str, Any]) -> List[str]:
        """Get list of required parameters"""
        return [name for name, info in parameters.items() if info.get("required", False)]
    
    def _get_typescript_type(self, json_type: str) -> str:
        """Convert JSON type to TypeScript type"""
        type_map = {
            "string": "string",
            "number": "number",
            "integer": "number",
            "boolean": "boolean",
            "array": "any[]",
            "object": "any"
        }
        return type_map.get(json_type, "any")
    
    def process_message(self, message: str) -> str:
        """Process incoming messages about infrastructure"""
        message_lower = message.lower()
        
        # Check if asking about available services
        if "what services" in message_lower or "available services" in message_lower:
            services = self.list_available_services()
            return f"I have Fort Knox documentation for these services: {', '.join(services)}"
        
        # Check if asking to analyze infrastructure
        if "analyze" in message_lower:
            analysis = self.analyze_infrastructure_needs()
            return f"Infrastructure analysis complete:\n- Available services: {list(analysis['available_services'].keys())}\n- Recommended tools to create: {len(analysis['recommended_tools'])}\n- Missing docs: {analysis['missing_documentation']}"
        
        # Check if asking to create a tool
        if "create tool" in message_lower:
            # Extract service and operation from message
            # This is a simple implementation - could be enhanced with NLP
            if "compute" in message_lower and "instance" in message_lower:
                result = self.create_infrastructure_tool("compute", "create_instance")
                return result
            elif "storage" in message_lower and "bucket" in message_lower:
                result = self.create_infrastructure_tool("storage", "create_bucket")
                return result
            else:
                return "Please specify which service and operation you want a tool for. Example: 'create tool for compute instance creation'"
        
        # Default response
        return f"Infrastructure Agent ready. I can analyze infrastructure needs, create tools, and manage resources. Current message: {message}"
    
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute infrastructure-related tasks"""
        task_type = task.get("type", "")
        
        if task_type == "create_tool":
            service = task.get("service", "")
            operation = task.get("operation", "")
            result = self.create_infrastructure_tool(service, operation)
            return {"status": "completed", "result": result}
        
        elif task_type == "analyze_infrastructure":
            analysis = self.analyze_infrastructure_needs()
            return {"status": "completed", "result": analysis}
        
        elif task_type == "list_services":
            services = self.list_available_services()
            return {"status": "completed", "result": services}
        
        else:
            return {"status": "error", "result": f"Unknown task type: {task_type}"}


# Agent initialization
if __name__ == "__main__":
    agent = InfrastructureAgent()
    print(f"Infrastructure Agent initialized: {agent.agent_id}")
    print(f"Capabilities: {agent.capabilities}")
    
    # Analyze infrastructure
    analysis = agent.analyze_infrastructure_needs()
    print(f"\nInfrastructure Analysis:")
    print(f"Available services: {list(analysis['available_services'].keys())}")
    print(f"Recommended tools: {len(analysis['recommended_tools'])}")

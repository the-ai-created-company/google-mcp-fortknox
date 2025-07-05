import json
import os
from typing import Dict, List, Any

def extract_api_tools(discovery_doc: Dict[str, Any], api_name: str) -> Dict[str, Any]:
    """Extract all endpoints from a discovery document and format as MCP tools"""
    
    tools = {}
    base_url = discovery_doc.get('baseUrl', '')
    
    # Helper function to process method
    def process_method(resource_name: str, method_name: str, method_info: Dict[str, Any], path_prefix: str = ''):
        tool_name = f"{api_name}_{resource_name}_{method_name}".replace('.', '_')
        
        # Build the full path
        method_path = method_info.get('path', '')
        full_path = f"{base_url}{method_path}"
        
        # Extract parameters
        parameters = method_info.get('parameters', {})
        required_params = []
        optional_params = []
        
        for param_name, param_info in parameters.items():
            if param_info.get('required', False):
                required_params.append(param_name)
            else:
                optional_params.append(param_name)
        
        # Create tool definition
        tool = {
            'name': tool_name,
            'description': method_info.get('description', f'{method_name} operation for {resource_name}'),
            'http_method': method_info.get('httpMethod', 'GET'),
            'path': full_path,
            'parameters': parameters,
            'required_parameters': required_params,
            'optional_parameters': optional_params,
            'scopes': method_info.get('scopes', []),
            'response': method_info.get('response', {}),
            'request': method_info.get('request', {})
        }
        
        tools[tool_name] = tool
    
    # Process resources recursively
    def process_resources(resources: Dict[str, Any], parent_name: str = ''):
        for resource_name, resource_info in resources.items():
            if isinstance(resource_info, dict):
                # Build full resource name
                full_resource_name = f"{parent_name}_{resource_name}" if parent_name else resource_name
                
                # Process methods in this resource
                methods = resource_info.get('methods', {})
                for method_name, method_info in methods.items():
                    process_method(full_resource_name, method_name, method_info)
                
                # Process sub-resources
                sub_resources = resource_info.get('resources', {})
                if sub_resources:
                    process_resources(sub_resources, full_resource_name)
    
    # Start processing from root resources
    resources = discovery_doc.get('resources', {})
    process_resources(resources)
    
    return tools

def build_all_mcp_tools():
    """Process all discovery documents and build MCP tools"""
    
    discovery_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'discovery-docs')
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'extracted-data')
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    all_tools = {}
    api_summary = {}
    
    # Process each discovery document
    for filename in os.listdir(discovery_dir):
        if filename.endswith('_discovery.json'):
            print(f"\nProcessing {filename}...")
            
            filepath = os.path.join(discovery_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    discovery_doc = json.load(f)
                
                # Extract API name and version
                api_name = discovery_doc.get('name', filename.replace('_discovery.json', ''))
                api_version = discovery_doc.get('version', 'v1')
                api_title = discovery_doc.get('title', api_name)
                api_description = discovery_doc.get('description', '')
                
                # Create API-specific directory
                api_dir = os.path.join(output_dir, api_name)
                os.makedirs(api_dir, exist_ok=True)
                
                # Extract tools
                tools = extract_api_tools(discovery_doc, api_name)
                
                if tools:
                    # Save tools to JSON file
                    tools_file = os.path.join(api_dir, f"{api_name}_{api_version}_tools.json")
                    with open(tools_file, 'w', encoding='utf-8') as f:
                        json.dump(tools, f, indent=2)
                    
                    # Save a summary file
                    summary = {
                        'api_name': api_name,
                        'api_version': api_version,
                        'api_title': api_title,
                        'api_description': api_description,
                        'base_url': discovery_doc.get('baseUrl', ''),
                        'tool_count': len(tools),
                        'tools_file': tools_file
                    }
                    
                    summary_file = os.path.join(api_dir, f"{api_name}_{api_version}_summary.json")
                    with open(summary_file, 'w', encoding='utf-8') as f:
                        json.dump(summary, f, indent=2)
                    
                    # Add to master tools collection
                    all_tools.update(tools)
                    
                    # Add to API summary
                    api_summary[api_name] = {
                        'version': api_version,
                        'title': api_title,
                        'tool_count': len(tools),
                        'base_url': discovery_doc.get('baseUrl', '')
                    }
                    
                    print(f"  [OK] Extracted {len(tools)} tools for {api_title}")
                else:
                    print(f"  [WARNING] No tools found for {api_name}")
                    
            except Exception as e:
                print(f"  [ERROR] Error processing {filename}: {e}")
    
    # Save master tools file
    master_tools_file = os.path.join(output_dir, 'all_google_cloud_tools.json')
    with open(master_tools_file, 'w', encoding='utf-8') as f:
        json.dump(all_tools, f, indent=2)
    
    # Save master summary
    master_summary = {
        'total_apis': len(api_summary),
        'total_tools': len(all_tools),
        'apis': api_summary,
        'generated_at': os.environ.get('USERNAME', 'system'),
        'tools_file': master_tools_file
    }
    
    master_summary_file = os.path.join(output_dir, 'master_summary.json')
    with open(master_summary_file, 'w', encoding='utf-8') as f:
        json.dump(master_summary, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"MCP Tool Generation Complete!")
    print(f"  Total APIs processed: {len(api_summary)}")
    print(f"  Total tools generated: {len(all_tools)}")
    print(f"  Output directory: {output_dir}")
    print(f"  Master tools file: {master_tools_file}")
    print(f"{'='*60}")
    
    # Create a TypeScript interface file for the tools
    create_typescript_interfaces(all_tools, output_dir)

def create_typescript_interfaces(tools: Dict[str, Any], output_dir: str):
    """Create TypeScript interfaces for the MCP tools"""
    
    ts_content = """// Auto-generated TypeScript interfaces for Google Cloud MCP Tools

export interface MCPTool {
  name: string;
  description: string;
  http_method: string;
  path: string;
  parameters: Record<string, ParameterInfo>;
  required_parameters: string[];
  optional_parameters: string[];
  scopes: string[];
  response?: any;
  request?: any;
}

export interface ParameterInfo {
  type: string;
  description?: string;
  location?: string;
  required?: boolean;
  default?: any;
  enum?: string[];
  enumDescriptions?: string[];
  minimum?: number;
  maximum?: number;
  pattern?: string;
}

export const GoogleCloudMCPTools: Record<string, MCPTool> = {
"""
    
    # Add each tool
    for tool_name, tool_info in tools.items():
        ts_content += f'  "{tool_name}": {json.dumps(tool_info, indent=2).replace(": true", ": true").replace(": false", ": false")},\n'
    
    ts_content += "};\n"
    
    # Save TypeScript file
    ts_file = os.path.join(output_dir, 'google_cloud_mcp_tools.ts')
    with open(ts_file, 'w', encoding='utf-8') as f:
        f.write(ts_content)
    
    print(f"\nCreated TypeScript interfaces at: {ts_file}")

if __name__ == "__main__":
    build_all_mcp_tools()

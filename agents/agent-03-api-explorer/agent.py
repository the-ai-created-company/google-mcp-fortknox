"""API Explorer Agent

This agent specializes in discovering and integrating external APIs by:
- Analyzing API documentation and endpoints
- Reverse engineering APIs through exploration
- Generating MCP tool wrappers automatically
- Testing API endpoints and monitoring health
- Creating comprehensive API documentation
"""

from pathlib import Path
import sys
import json
import requests
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import re

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base_agent import BaseAgent


class APIExplorerAgent(BaseAgent):
    """Agent specialized in discovering and integrating external APIs"""
    
    def __init__(self):
        super().__init__(
            agent_id="agent-03-api-explorer",
            name="API Explorer",
            capabilities=[
                "discover_api",
                "analyze_endpoints",
                "generate_api_wrapper",
                "test_endpoints",
                "monitor_api_health",
                "create_api_documentation",
                "detect_api_patterns",
                "handle_authentication"
            ]
        )
        self.discovered_apis = {}
        self.api_patterns = self._load_api_patterns()
    
    def _load_api_patterns(self) -> Dict[str, Any]:
        """Load common API patterns for detection"""
        return {
            "rest": {
                "indicators": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                "patterns": {
                    "resource_list": r"^/api/v\d+/\w+/?$",
                    "resource_detail": r"^/api/v\d+/\w+/[\w-]+/?$",
                    "nested_resource": r"^/api/v\d+/\w+/[\w-]+/\w+/?$"
                }
            },
            "graphql": {
                "indicators": ["query", "mutation", "subscription"],
                "endpoints": ["/graphql", "/api/graphql", "/v1/graphql"]
            },
            "auth_patterns": {
                "bearer": r"Bearer\s+[\w-]+",
                "api_key": r"[Xx]-[Aa]pi-[Kk]ey",
                "basic": r"Basic\s+[\w=]+",
                "oauth": r"oauth_[\w]+="
            }
        }
    
    def discover_api(self, api_url: str, auth_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Discover and analyze an API"""
        discovery_result = {
            "url": api_url,
            "type": "unknown",
            "endpoints": [],
            "authentication": {},
            "documentation": {},
            "patterns_detected": [],
            "suggested_tools": []
        }
        
        # Parse URL
        parsed_url = urlparse(api_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Try to find API documentation
        doc_endpoints = self._find_documentation_endpoints(base_url)
        if doc_endpoints:
            discovery_result["documentation"] = doc_endpoints
        
        # Detect API type
        api_type = self._detect_api_type(api_url, auth_config)
        discovery_result["type"] = api_type
        
        # Discover endpoints based on type
        if api_type == "rest":
            endpoints = self._discover_rest_endpoints(api_url, auth_config)
        elif api_type == "graphql":
            endpoints = self._discover_graphql_schema(api_url, auth_config)
        else:
            endpoints = self._probe_common_endpoints(base_url, auth_config)
        
        discovery_result["endpoints"] = endpoints
        
        # Analyze authentication
        auth_method = self._detect_authentication(api_url, auth_config)
        discovery_result["authentication"] = auth_method
        
        # Generate tool suggestions
        discovery_result["suggested_tools"] = self._suggest_tools(endpoints, api_type)
        
        # Store discovery results
        self.discovered_apis[api_url] = discovery_result
        self.store_knowledge(f"api_discovery_{parsed_url.netloc}", discovery_result, "discovered_apis")
        
        return discovery_result
    
    def _find_documentation_endpoints(self, base_url: str) -> Dict[str, str]:
        """Look for common API documentation endpoints"""
        doc_paths = [
            "/docs", "/api/docs", "/api-docs", "/swagger", 
            "/swagger.json", "/openapi.json", "/api/swagger.json",
            "/redoc", "/graphql", "/.well-known/openapi.json",
            "/api", "/developers", "/api/v1"
        ]
        
        found_docs = {}
        
        for path in doc_paths:
            try:
                response = requests.head(base_url + path, timeout=5, allow_redirects=True)
                if response.status_code < 400:
                    found_docs[path] = base_url + path
            except:
                pass
        
        return found_docs
    
    def _detect_api_type(self, api_url: str, auth_config: Optional[Dict[str, Any]] = None) -> str:
        """Detect the type of API (REST, GraphQL, etc.)"""
        headers = self._prepare_headers(auth_config)
        
        # Check for GraphQL
        for endpoint in self.api_patterns["graphql"]["endpoints"]:
            try:
                test_url = api_url.rstrip('/') + endpoint
                response = requests.post(
                    test_url,
                    json={"query": "{__schema{types{name}}}"},
                    headers=headers,
                    timeout=5
                )
                if response.status_code == 200 and "__schema" in response.text:
                    return "graphql"
            except:
                pass
        
        # Check for REST patterns
        try:
            response = requests.options(api_url, headers=headers, timeout=5)
            if "Allow" in response.headers:
                methods = response.headers["Allow"].upper()
                rest_methods = set(self.api_patterns["rest"]["indicators"])
                if any(method in methods for method in rest_methods):
                    return "rest"
        except:
            pass
        
        # Default to REST
        return "rest"
    
    def _prepare_headers(self, auth_config: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """Prepare request headers with authentication"""
        headers = {
            "User-Agent": "Fort-Knox-API-Explorer/1.0",
            "Accept": "application/json"
        }
        
        if auth_config:
            auth_type = auth_config.get("type", "")
            
            if auth_type == "bearer":
                headers["Authorization"] = f"Bearer {auth_config.get('token', '')}"
            elif auth_type == "api_key":
                key_name = auth_config.get("key_name", "X-API-Key")
                headers[key_name] = auth_config.get("key_value", "")
            elif auth_type == "basic":
                import base64
                credentials = f"{auth_config.get('username', '')}:{auth_config.get('password', '')}"
                encoded = base64.b64encode(credentials.encode()).decode()
                headers["Authorization"] = f"Basic {encoded}"
        
        return headers
    
    def _discover_rest_endpoints(self, api_url: str, auth_config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Discover REST API endpoints"""
        endpoints = []
        headers = self._prepare_headers(auth_config)
        
        # Try to get OpenAPI/Swagger spec first
        spec_urls = [
            api_url.rstrip('/') + "/openapi.json",
            api_url.rstrip('/') + "/swagger.json",
            api_url.rstrip('/') + "/api-docs"
        ]
        
        for spec_url in spec_urls:
            try:
                response = requests.get(spec_url, headers=headers, timeout=5)
                if response.status_code == 200:
                    spec = response.json()
                    endpoints.extend(self._parse_openapi_spec(spec))
                    return endpoints
            except:
                pass
        
        # Fallback to probing common patterns
        return self._probe_common_endpoints(api_url, auth_config)
    
    def _parse_openapi_spec(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse OpenAPI/Swagger specification"""
        endpoints = []
        
        paths = spec.get("paths", {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    endpoint = {
                        "path": path,
                        "method": method.upper(),
                        "summary": details.get("summary", ""),
                        "description": details.get("description", ""),
                        "parameters": details.get("parameters", []),
                        "requestBody": details.get("requestBody", {}),
                        "responses": details.get("responses", {})
                    }
                    endpoints.append(endpoint)
        
        return endpoints
    
    def _discover_graphql_schema(self, api_url: str, auth_config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Discover GraphQL schema"""
        headers = self._prepare_headers(auth_config)
        introspection_query = """
        query IntrospectionQuery {
          __schema {
            queryType { name }
            mutationType { name }
            types {
              ...FullType
            }
          }
        }
        
        fragment FullType on __Type {
          kind
          name
          description
          fields(includeDeprecated: true) {
            name
            description
            args {
              ...InputValue
            }
            type {
              ...TypeRef
            }
          }
        }
        
        fragment InputValue on __InputValue {
          name
          description
          type { ...TypeRef }
          defaultValue
        }
        
        fragment TypeRef on __Type {
          kind
          name
          ofType {
            kind
            name
          }
        }
        """
        
        try:
            response = requests.post(
                api_url,
                json={"query": introspection_query},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                schema = response.json()
                return self._parse_graphql_schema(schema)
        except:
            pass
        
        return []
    
    def _parse_graphql_schema(self, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse GraphQL schema into endpoints"""
        endpoints = []
        
        if "data" in schema and "__schema" in schema["data"]:
            types = schema["data"]["__schema"]["types"]
            
            for type_def in types:
                if type_def["name"] in ["Query", "Mutation"]:
                    for field in type_def.get("fields", []):
                        endpoint = {
                            "type": "graphql",
                            "operation": type_def["name"].lower(),
                            "name": field["name"],
                            "description": field.get("description", ""),
                            "args": field.get("args", [])
                        }
                        endpoints.append(endpoint)
        
        return endpoints
    
    def _probe_common_endpoints(self, base_url: str, auth_config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Probe for common API endpoints"""
        endpoints = []
        headers = self._prepare_headers(auth_config)
        
        common_paths = [
            "/api", "/api/v1", "/api/v2", "/v1", "/v2",
            "/users", "/api/users", "/api/v1/users",
            "/products", "/api/products", "/api/v1/products",
            "/auth", "/api/auth", "/api/v1/auth",
            "/health", "/api/health", "/status"
        ]
        
        for path in common_paths:
            try:
                url = base_url.rstrip('/') + path
                response = requests.get(url, headers=headers, timeout=5)
                
                if response.status_code < 400:
                    endpoint = {
                        "path": path,
                        "method": "GET",
                        "status_code": response.status_code,
                        "content_type": response.headers.get("Content-Type", ""),
                        "discovered": True
                    }
                    
                    # Try to detect response structure
                    try:
                        data = response.json()
                        endpoint["response_structure"] = self._analyze_json_structure(data)
                    except:
                        pass
                    
                    endpoints.append(endpoint)
            except:
                pass
        
        return endpoints
    
    def _analyze_json_structure(self, data: Any, max_depth: int = 3, current_depth: int = 0) -> Dict[str, Any]:
        """Analyze JSON response structure"""
        if current_depth >= max_depth:
            return {"type": "object", "truncated": True}
        
        if isinstance(data, dict):
            return {
                "type": "object",
                "properties": {
                    k: self._analyze_json_structure(v, max_depth, current_depth + 1)
                    for k, v in list(data.items())[:10]  # Limit to 10 properties
                }
            }
        elif isinstance(data, list):
            if data:
                return {
                    "type": "array",
                    "items": self._analyze_json_structure(data[0], max_depth, current_depth + 1)
                }
            return {"type": "array", "items": {"type": "unknown"}}
        elif isinstance(data, str):
            return {"type": "string", "example": data[:50]}
        elif isinstance(data, (int, float)):
            return {"type": "number", "example": data}
        elif isinstance(data, bool):
            return {"type": "boolean", "example": data}
        else:
            return {"type": "null"}
    
    def _detect_authentication(self, api_url: str, auth_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Detect authentication method required by API"""
        auth_info = {
            "required": False,
            "type": "none",
            "details": {}
        }
        
        # Test without auth first
        try:
            response = requests.get(api_url, timeout=5)
            
            # Check for auth headers in response
            if response.status_code == 401:
                auth_info["required"] = True
                
                # Check WWW-Authenticate header
                if "WWW-Authenticate" in response.headers:
                    auth_header = response.headers["WWW-Authenticate"]
                    if "Bearer" in auth_header:
                        auth_info["type"] = "bearer"
                    elif "Basic" in auth_header:
                        auth_info["type"] = "basic"
                    auth_info["details"]["header"] = auth_header
            
            # Check for API key indicators
            if "X-API-Key" in response.headers or response.status_code == 403:
                auth_info["type"] = "api_key"
                auth_info["required"] = True
        
        except:
            pass
        
        return auth_info
    
    def _suggest_tools(self, endpoints: List[Dict[str, Any]], api_type: str) -> List[Dict[str, Any]]:
        """Suggest MCP tools to create based on discovered endpoints"""
        suggestions = []
        
        if api_type == "rest":
            # Group endpoints by resource
            resources = {}
            for endpoint in endpoints:
                path = endpoint.get("path", "")
                parts = path.strip("/").split("/")
                if parts:
                    resource = parts[-1] if parts[-1] not in ["v1", "v2", "api"] else parts[-2] if len(parts) > 1 else "general"
                    if resource not in resources:
                        resources[resource] = []
                    resources[resource].append(endpoint)
            
            # Suggest CRUD tools for each resource
            for resource, resource_endpoints in resources.items():
                methods = set(ep.get("method", "GET") for ep in resource_endpoints)
                if len(methods) >= 3:  # Has multiple operations
                    suggestions.append({
                        "name": f"{resource}_crud_tool",
                        "type": "crud",
                        "resource": resource,
                        "operations": list(methods)
                    })
                else:
                    for endpoint in resource_endpoints:
                        suggestions.append({
                            "name": f"{resource}_{endpoint.get('method', 'get').lower()}_tool",
                            "type": "single",
                            "endpoint": endpoint
                        })
        
        elif api_type == "graphql":
            # Suggest tools for queries and mutations
            queries = [ep for ep in endpoints if ep.get("operation") == "query"]
            mutations = [ep for ep in endpoints if ep.get("operation") == "mutation"]
            
            if queries:
                suggestions.append({
                    "name": "graphql_query_tool",
                    "type": "graphql_query",
                    "operations": [q["name"] for q in queries[:10]]
                })
            
            if mutations:
                suggestions.append({
                    "name": "graphql_mutation_tool",
                    "type": "graphql_mutation",
                    "operations": [m["name"] for m in mutations[:10]]
                })
        
        return suggestions
    
    def generate_api_wrapper(self, api_url: str, tool_name: str, endpoints: List[Dict[str, Any]], auth_config: Optional[Dict[str, Any]] = None) -> str:
        """Generate MCP tool wrapper for API"""
        # Use discovery results if available
        if api_url in self.discovered_apis:
            api_info = self.discovered_apis[api_url]
            api_type = api_info["type"]
        else:
            api_type = "rest"
        
        if api_type == "graphql":
            tool_code = self._generate_graphql_tool(tool_name, api_url, endpoints, auth_config)
        else:
            tool_code = self._generate_rest_tool(tool_name, api_url, endpoints, auth_config)
        
        # Create the tool
        result = self.create_mcp_tool(tool_name, tool_code, "external-apis")
        
        # Store tool info
        self.store_knowledge(
            f"api_tool_{tool_name}",
            {
                "api_url": api_url,
                "api_type": api_type,
                "endpoints": endpoints,
                "created_by": self.agent_id
            },
            category="api_tools"
        )
        
        return result
    
    def _generate_rest_tool(self, tool_name: str, api_url: str, endpoints: List[Dict[str, Any]], auth_config: Optional[Dict[str, Any]] = None) -> str:
        """Generate REST API tool code"""
        # Group endpoints by resource
        resources = {}
        for endpoint in endpoints:
            path = endpoint.get("path", "")
            method = endpoint.get("method", "GET")
            
            # Extract resource name
            parts = path.strip("/").split("/")
            resource = "general"
            for part in reversed(parts):
                if part and not part.startswith("{") and part not in ["api", "v1", "v2"]:
                    resource = part
                    break
            
            if resource not in resources:
                resources[resource] = []
            resources[resource].append(endpoint)
        
        # Generate tool code
        tool_code = f"""import {{ Tool }} from '@modelcontextprotocol/sdk';
import {{ z }} from 'zod';
import axios from 'axios';

// Auto-generated API wrapper for {api_url}
// Generated by API Explorer Agent

const API_BASE_URL = '{api_url}';

class {tool_name.replace('_', '')}API {{
  private headers: any = {{
    'Content-Type': 'application/json',
    'Accept': 'application/json'{self._generate_auth_headers(auth_config)}
  }};

"""
        
        # Generate methods for each endpoint
        for resource, resource_endpoints in resources.items():
            tool_code += f"\n  // {resource.title()} operations\n"
            
            for endpoint in resource_endpoints:
                method_name = self._generate_method_name(endpoint)
                tool_code += self._generate_method(method_name, endpoint)
        
        tool_code += "}\n\n"
        
        # Generate MCP tool exports
        tool_code += f"const apiClient = new {tool_name.replace('_', '')}API();\n\n"
        
        # Export tools for each method
        for resource, resource_endpoints in resources.items():
            for endpoint in resource_endpoints:
                method_name = self._generate_method_name(endpoint)
                tool_code += self._generate_tool_export(tool_name, method_name, endpoint)
        
        return tool_code
    
    def _generate_auth_headers(self, auth_config: Optional[Dict[str, Any]]) -> str:
        """Generate authentication headers"""
        if not auth_config:
            return ""
        
        auth_type = auth_config.get("type", "")
        
        if auth_type == "bearer":
            return f",\n    'Authorization': 'Bearer {auth_config.get('token', 'YOUR_TOKEN_HERE')}'"
        elif auth_type == "api_key":
            key_name = auth_config.get("key_name", "X-API-Key")
            return f",\n    '{key_name}': '{auth_config.get('key_value', 'YOUR_API_KEY_HERE')}'"
        elif auth_type == "basic":
            return f",\n    'Authorization': 'Basic {auth_config.get('credentials', 'YOUR_CREDENTIALS_HERE')}'"
        
        return ""
    
    def _generate_method_name(self, endpoint: Dict[str, Any]) -> str:
        """Generate method name from endpoint"""
        method = endpoint.get("method", "GET").lower()
        path = endpoint.get("path", "")
        
        # Clean path
        parts = [p for p in path.strip("/").split("/") if p and not p.startswith("{") and p not in ["api", "v1", "v2"]]
        
        if parts:
            resource = parts[-1]
            return f"{method}_{resource}"
        else:
            return f"{method}_request"
    
    def _generate_method(self, method_name: str, endpoint: Dict[str, Any]) -> str:
        """Generate method implementation"""
        method = endpoint.get("method", "GET")
        path = endpoint.get("path", "")
        parameters = endpoint.get("parameters", [])
        
        # Extract path parameters
        path_params = re.findall(r'\{(\w+)\}', path)
        
        # Generate method signature
        params = []
        if path_params:
            params.extend([f"{param}: string" for param in path_params])
        if method in ["POST", "PUT", "PATCH"]:
            params.append("data: any")
        if parameters:
            query_params = [p for p in parameters if p.get("in") == "query"]
            if query_params:
                params.append("queryParams?: any")
        
        param_str = ", ".join(params) if params else ""
        
        # Generate method
        method_code = f"""
  async {method_name}({param_str}) {{
    try {{
      const url = `${{API_BASE_URL}}{path}`"""
        
        # Replace path parameters
        for param in path_params:
            method_code = method_code.replace(f"{{{param}}}", f"${{{param}}}")
        
        method_code += ";"
        
        # Add request
        if method == "GET":
            method_code += """
      const response = await axios.get(url, {
        headers: this.headers,
        params: queryParams
      });"""
        else:
            method_code += f"""
      const response = await axios.{method.lower()}(url, data, {{
        headers: this.headers,
        params: queryParams
      }});"""
        
        method_code += """
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
"""
        
        return method_code
    
    def _generate_tool_export(self, tool_name: str, method_name: str, endpoint: Dict[str, Any]) -> str:
        """Generate MCP tool export"""
        description = endpoint.get("summary", endpoint.get("description", f"{endpoint.get('method', 'GET')} {endpoint.get('path', '')}"))
        
        return f"""
export const {tool_name}_{method_name}: Tool = {{
  name: '{tool_name}_{method_name}',
  description: '{description}',
  inputSchema: z.object({{
    // TODO: Define proper schema based on endpoint parameters
  }}),
  async execute(params) {{
    return await apiClient.{method_name}(params);
  }}
}};
"""
    
    def _generate_graphql_tool(self, tool_name: str, api_url: str, operations: List[Dict[str, Any]], auth_config: Optional[Dict[str, Any]] = None) -> str:
        """Generate GraphQL API tool code"""
        queries = [op for op in operations if op.get("operation") == "query"]
        mutations = [op for op in operations if op.get("operation") == "mutation"]
        
        tool_code = f"""import {{ Tool }} from '@modelcontextprotocol/sdk';
import {{ z }} from 'zod';
import {{ GraphQLClient }} from 'graphql-request';

// Auto-generated GraphQL API wrapper for {api_url}
// Generated by API Explorer Agent

const client = new GraphQLClient('{api_url}', {{
  headers: {{
    'Content-Type': 'application/json'{self._generate_auth_headers(auth_config)}
  }}
}});

"""
        
        # Generate query tools
        if queries:
            tool_code += "// Query operations\n"
            for query in queries[:10]:  # Limit to 10
                tool_code += self._generate_graphql_operation_tool(tool_name, query, "query")
        
        # Generate mutation tools
        if mutations:
            tool_code += "\n// Mutation operations\n"
            for mutation in mutations[:10]:  # Limit to 10
                tool_code += self._generate_graphql_operation_tool(tool_name, mutation, "mutation")
        
        return tool_code
    
    def _generate_graphql_operation_tool(self, tool_name: str, operation: Dict[str, Any], op_type: str) -> str:
        """Generate GraphQL operation tool"""
        op_name = operation.get("name", "operation")
        description = operation.get("description", f"GraphQL {op_type}: {op_name}")
        args = operation.get("args", [])
        
        # Build argument schema
        schema_props = {}
        for arg in args:
            arg_name = arg.get("name", "arg")
            schema_props[arg_name] = "z.any()"  # Simplified - should analyze type
        
        schema_str = "z.object({" + ", ".join([f"{k}: {v}" for k, v in schema_props.items()]) + "})" if schema_props else "z.object({})"
        
        return f"""
export const {tool_name}_{op_name}: Tool = {{
  name: '{tool_name}_{op_name}',
  description: '{description}',
  inputSchema: {schema_str},
  async execute(params) {{
    try {{
      const {op_type} = `
        {op_type} {op_name}(${{Object.keys(params).map(k => `$${k}: Any`).join(', ')}}) {{
          {op_name}(${{Object.keys(params).map(k => `${k}: $${k}`).join(', ')}}) {{
            // TODO: Add return fields
          }}
        }}
      `;
      
      const result = await client.request({op_type}, params);
      return {{ success: true, data: result }};
    }} catch (error) {{
      return {{ success: false, error: error.message }};
    }}
  }}
}};
"""
    
    def test_api_endpoint(self, api_url: str, method: str = "GET", data: Optional[Any] = None, auth_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Test an API endpoint"""
        headers = self._prepare_headers(auth_config)
        
        try:
            if method.upper() == "GET":
                response = requests.get(api_url, headers=headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(api_url, json=data, headers=headers, timeout=10)
            elif method.upper() == "PUT":
                response = requests.put(api_url, json=data, headers=headers, timeout=10)
            elif method.upper() == "DELETE":
                response = requests.delete(api_url, headers=headers, timeout=10)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            result = {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "response_time": response.elapsed.total_seconds()
            }
            
            try:
                result["data"] = response.json()
            except:
                result["data"] = response.text[:1000]  # Limit text response
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def monitor_api_health(self, api_url: str, endpoints: List[str], auth_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Monitor health of API endpoints"""
        health_report = {
            "api_url": api_url,
            "timestamp": self._get_timestamp(),
            "overall_health": "healthy",
            "endpoints": []
        }
        
        failed_count = 0
        
        for endpoint in endpoints:
            result = self.test_api_endpoint(
                api_url.rstrip('/') + endpoint,
                auth_config=auth_config
            )
            
            endpoint_health = {
                "endpoint": endpoint,
                "status": "healthy" if result["success"] else "unhealthy",
                "response_time": result.get("response_time", -1),
                "status_code": result.get("status_code", 0)
            }
            
            if not result["success"]:
                failed_count += 1
                endpoint_health["error"] = result.get("error", "Unknown error")
            
            health_report["endpoints"].append(endpoint_health)
        
        # Determine overall health
        if failed_count == 0:
            health_report["overall_health"] = "healthy"
        elif failed_count < len(endpoints) / 2:
            health_report["overall_health"] = "degraded"
        else:
            health_report["overall_health"] = "unhealthy"
        
        # Store health report
        self.store_knowledge(
            f"api_health_{urlparse(api_url).netloc}",
            health_report,
            category="api_health"
        )
        
        return health_report
    
    def create_api_documentation(self, api_url: str, discovery_result: Optional[Dict[str, Any]] = None) -> str:
        """Create documentation for discovered API"""
        if discovery_result is None:
            if api_url in self.discovered_apis:
                discovery_result = self.discovered_apis[api_url]
            else:
                return "No discovery results found for this API"
        
        # Generate markdown documentation
        doc = f"""# API Documentation: {api_url}

## Overview
- **Type**: {discovery_result.get('type', 'Unknown')}
- **Authentication**: {discovery_result.get('authentication', {}).get('type', 'None')}
- **Discovered**: {self._get_timestamp()}

## Authentication
"""
        
        auth = discovery_result.get('authentication', {})
        if auth.get('required'):
            doc += f"- **Required**: Yes\n"
            doc += f"- **Type**: {auth.get('type', 'Unknown')}\n"
            if auth.get('details'):
                doc += f"- **Details**: {json.dumps(auth.get('details'), indent=2)}\n"
        else:
            doc += "- **Required**: No\n"
        
        doc += "\n## Endpoints\n"
        
        # Document endpoints
        endpoints = discovery_result.get('endpoints', [])
        for endpoint in endpoints:
            if discovery_result.get('type') == 'graphql':
                doc += f"\n### {endpoint.get('operation', 'operation').title()}: {endpoint.get('name', 'Unknown')}\n"
                doc += f"- **Type**: {endpoint.get('operation', 'Unknown')}\n"
                doc += f"- **Description**: {endpoint.get('description', 'No description')}\n"
                
                args = endpoint.get('args', [])
                if args:
                    doc += "- **Arguments**:\n"
                    for arg in args:
                        doc += f"  - `{arg.get('name', 'arg')}`: {arg.get('type', {}).get('name', 'Any')}\n"
            else:
                doc += f"\n### {endpoint.get('method', 'GET')} {endpoint.get('path', '/')}\n"
                doc += f"- **Summary**: {endpoint.get('summary', 'No summary')}\n"
                doc += f"- **Description**: {endpoint.get('description', 'No description')}\n"
                
                params = endpoint.get('parameters', [])
                if params:
                    doc += "- **Parameters**:\n"
                    for param in params:
                        doc += f"  - `{param.get('name', 'param')}` ({param.get('in', 'query')}): {param.get('description', 'No description')}\n"
        
        doc += "\n## Suggested Tools\n"
        
        tools = discovery_result.get('suggested_tools', [])
        for tool in tools:
            doc += f"- **{tool.get('name', 'tool')}**: {tool.get('type', 'Unknown')} tool"
            if 'operations' in tool:
                doc += f" with operations: {', '.join(tool['operations'])}"
            doc += "\n"
        
        # Save documentation
        doc_path = self.repo_root / "fort-knox-apis" / "external-apis" / f"{urlparse(api_url).netloc}.md"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text(doc)
        
        return f"Documentation created at: {doc_path}"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def process_message(self, message: str) -> str:
        """Process incoming messages about API exploration"""
        message_lower = message.lower()
        
        # Check if asking to discover an API
        if "discover" in message_lower or "explore" in message_lower:
            # Extract URL from message
            url_pattern = r'https?://[^\s]+'
            urls = re.findall(url_pattern, message)
            
            if urls:
                api_url = urls[0]
                result = self.discover_api(api_url)
                return f"Discovered {result['type']} API with {len(result['endpoints'])} endpoints. Authentication: {result['authentication']['type']}. Suggested {len(result['suggested_tools'])} tools."
            else:
                return "Please provide an API URL to discover. Example: 'discover https://api.example.com'"
        
        # Check if asking to create wrapper
        if "create" in message_lower and ("wrapper" in message_lower or "tool" in message_lower):
            # Look for discovered APIs
            if self.discovered_apis:
                api_url = list(self.discovered_apis.keys())[0]  # Use first discovered API
                discovery = self.discovered_apis[api_url]
                
                if discovery['suggested_tools']:
                    tool = discovery['suggested_tools'][0]
                    result = self.generate_api_wrapper(
                        api_url,
                        tool['name'],
                        discovery['endpoints'][:5]  # Limit to 5 endpoints
                    )
                    return f"Created API wrapper: {result}"
                else:
                    return "No tools suggested for discovered APIs"
            else:
                return "Please discover an API first using 'discover [URL]'"
        
        # Check if asking to test endpoint
        if "test" in message_lower:
            urls = re.findall(r'https?://[^\s]+', message)
            if urls:
                result = self.test_api_endpoint(urls[0])
                return f"Test result: Status {result.get('status_code', 'N/A')}, Success: {result['success']}"
            else:
                return "Please provide an endpoint URL to test"
        
        # Check if asking about health
        if "health" in message_lower or "monitor" in message_lower:
            if self.discovered_apis:
                api_url = list(self.discovered_apis.keys())[0]
                endpoints = [ep['path'] for ep in self.discovered_apis[api_url]['endpoints'][:5]]
                result = self.monitor_api_health(api_url, endpoints)
                return f"API Health: {result['overall_health']}. Tested {len(result['endpoints'])} endpoints."
            else:
                return "Please discover an API first to monitor its health"
        
        return f"API Explorer ready. I can discover APIs, create wrappers, test endpoints, and monitor health. Message: {message}"
    
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute API exploration tasks"""
        task_type = task.get("type", "")
        
        if task_type == "discover_api":
            api_url = task.get("api_url", "")
            auth_config = task.get("auth_config")
            result = self.discover_api(api_url, auth_config)
            return {"status": "completed", "result": result}
        
        elif task_type == "generate_wrapper":
            api_url = task.get("api_url", "")
            tool_name = task.get("tool_name", "api_tool")
            endpoints = task.get("endpoints", [])
            auth_config = task.get("auth_config")
            result = self.generate_api_wrapper(api_url, tool_name, endpoints, auth_config)
            return {"status": "completed", "result": result}
        
        elif task_type == "test_endpoint":
            endpoint_url = task.get("endpoint_url", "")
            method = task.get("method", "GET")
            data = task.get("data")
            auth_config = task.get("auth_config")
            result = self.test_api_endpoint(endpoint_url, method, data, auth_config)
            return {"status": "completed", "result": result}
        
        elif task_type == "monitor_health":
            api_url = task.get("api_url", "")
            endpoints = task.get("endpoints", [])
            auth_config = task.get("auth_config")
            result = self.monitor_api_health(api_url, endpoints, auth_config)
            return {"status": "completed", "result": result}
        
        elif task_type == "create_documentation":
            api_url = task.get("api_url", "")
            result = self.create_api_documentation(api_url)
            return {"status": "completed", "result": result}
        
        else:
            return {"status": "error", "result": f"Unknown task type: {task_type}"}


# Agent initialization
if __name__ == "__main__":
    agent = APIExplorerAgent()
    print(f"API Explorer Agent initialized: {agent.agent_id}")
    print(f"Capabilities: {agent.capabilities}")
    
    # Test API discovery
    test_url = "https://api.github.com"
    print(f"\nTesting API discovery on {test_url}...")
    result = agent.discover_api(test_url)
    print(f"Discovered: {result['type']} API")
    print(f"Endpoints found: {len(result['endpoints'])}")
    print(f"Authentication: {result['authentication']}")
    print(f"Suggested tools: {len(result['suggested_tools'])}")

#!/usr/bin/env python3
"""
MCP Factory - Dynamic tool generation from Google Cloud blueprints
Generates MCP tools on-demand from 2,953 Google Cloud operations
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional
from fastmcp import FastMCP
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Google Cloud MCP Factory")

# Global blueprint storage
blueprints: Dict[str, Dict[str, Any]] = {}
openwebui_tools: Dict[str, Any] = {}

def load_blueprints():
    """Load all blueprints from the filesystem on startup."""
    global blueprints, openwebui_tools
    
    blueprint_dir = os.getenv("BLUEPRINTS_PATH", "/app/blueprints")
    logger.info(f"Loading blueprints from: {blueprint_dir}")
    
    # Load Google Cloud blueprints
    if os.path.exists(blueprint_dir):
        for service_dir in os.listdir(blueprint_dir):
            service_path = os.path.join(blueprint_dir, service_dir)
            if os.path.isdir(service_path):
                endpoints_file = os.path.join(service_path, "api_endpoints.json")
                if os.path.exists(endpoints_file):
                    try:
                        with open(endpoints_file, 'r') as f:
                            blueprints[service_dir] = json.load(f)
                            operation_count = sum(
                                len(ops) for ops in blueprints[service_dir].values()
                            )
                            logger.info(f"Loaded {service_dir}: {operation_count} operations")
                    except Exception as e:
                        logger.error(f"Failed to load {service_dir}: {e}")
    
    # Load Open WebUI control tools
    openwebui_path = "/app/openwebui-control/tools.json"
    if os.path.exists(openwebui_path):
        try:
            with open(openwebui_path, 'r') as f:
                openwebui_tools = json.load(f)
                logger.info(f"Loaded Open WebUI tools: {len(openwebui_tools)} operations")
        except Exception as e:
            logger.error(f"Failed to load Open WebUI tools: {e}")
    
    total_google = sum(
        sum(len(ops) for ops in service.values()) 
        for service in blueprints.values()
    )
    logger.info(f"Total blueprints loaded: {total_google} Google Cloud + {len(openwebui_tools)} Open WebUI")

@mcp.tool
def list_available_services() -> Dict[str, Any]:
    """List all available services with operation counts."""
    services = {}
    
    # Google Cloud services
    for service_name, service_data in blueprints.items():
        operation_count = sum(len(ops) for ops in service_data.values())
        services[service_name] = {
            "type": "google_cloud",
            "operations": operation_count,
            "categories": list(service_data.keys())
        }
    
    # Open WebUI service
    if openwebui_tools:
        services["openwebui"] = {
            "type": "open_webui",
            "operations": len(openwebui_tools),
            "categories": ["control", "management"]
        }
    
    return {
        "services": services,
        "total_services": len(services),
        "total_operations": sum(s["operations"] for s in services.values())
    }

@mcp.tool
def list_service_operations(service: str, category: Optional[str] = None) -> Dict[str, Any]:
    """List all operations for a specific service."""
    if service == "openwebui":
        return {
            "service": service,
            "operations": list(openwebui_tools.keys()),
            "count": len(openwebui_tools)
        }
    
    if service not in blueprints:
        return {"error": f"Service '{service}' not found"}
    
    if category:
        if category not in blueprints[service]:
            return {"error": f"Category '{category}' not found in service '{service}'"}
        operations = list(blueprints[service][category].keys())
    else:
        operations = []
        for cat_ops in blueprints[service].values():
            operations.extend(cat_ops.keys())
    
    return {
        "service": service,
        "category": category,
        "operations": operations,
        "count": len(operations)
    }

@mcp.tool
def get_operation_details(service: str, operation_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific operation."""
    if service == "openwebui" and operation_id in openwebui_tools:
        return openwebui_tools[operation_id]
    
    if service not in blueprints:
        return {"error": f"Service '{service}' not found"}
    
    for category, operations in blueprints[service].items():
        if operation_id in operations:
            return {
                "service": service,
                "category": category,
                "operation_id": operation_id,
                **operations[operation_id]
            }
    
    return {"error": f"Operation '{operation_id}' not found in service '{service}'"}

@mcp.tool
def create_google_cloud_tool(service: str, operation_id: str) -> Dict[str, Any]:
    """Generate an MCP tool from a Google Cloud blueprint."""
    if service not in blueprints:
        return {"success": False, "error": f"Service '{service}' not found"}
    
    for category, operations in blueprints[service].items():
        if operation_id in operations:
            op_data = operations[operation_id]
            
            # Generate the MCP tool definition
            tool_def = {
                "name": f"{service}_{operation_id}",
                "description": op_data.get("description", f"Execute {operation_id} operation"),
                "service": service,
                "category": category,
                "method": op_data.get("http_method", "GET"),
                "path": op_data.get("path_template", ""),
                "parameters": op_data.get("parameters", {}),
                "request_schema": op_data.get("request", {}),
                "response_schema": op_data.get("response", {}),
                "scopes": op_data.get("scopes", [])
            }
            
            return {
                "success": True,
                "tool": tool_def,
                "message": f"Tool '{service}_{operation_id}' created successfully"
            }
    
    return {"success": False, "error": f"Operation '{operation_id}' not found in service '{service}'"}

@mcp.tool
def create_openwebui_tool(operation_id: str) -> Dict[str, Any]:
    """Generate an MCP tool for Open WebUI control."""
    if operation_id not in openwebui_tools:
        return {"success": False, "error": f"Open WebUI operation '{operation_id}' not found"}
    
    tool_data = openwebui_tools[operation_id]
    
    # Generate the MCP tool definition
    tool_def = {
        "name": f"openwebui_{operation_id}",
        "description": tool_data.get("description", f"Execute {operation_id} operation"),
        "service": "openwebui",
        "endpoint": tool_data.get("endpoint", ""),
        "method": tool_data.get("method", "GET"),
        "parameters": tool_data.get("parameters", {}),
        "authentication": tool_data.get("authentication", "bearer")
    }
    
    return {
        "success": True,
        "tool": tool_def,
        "message": f"Open WebUI tool '{operation_id}' created successfully"
    }

@mcp.tool
def search_operations(query: str, limit: int = 10) -> Dict[str, Any]:
    """Search for operations across all services."""
    results = []
    query_lower = query.lower()
    
    # Search Google Cloud operations
    for service_name, service_data in blueprints.items():
        for category, operations in service_data.items():
            for op_id, op_data in operations.items():
                if (query_lower in op_id.lower() or 
                    query_lower in op_data.get("description", "").lower()):
                    results.append({
                        "service": service_name,
                        "category": category,
                        "operation_id": op_id,
                        "description": op_data.get("description", ""),
                        "method": op_data.get("http_method", "GET")
                    })
                    if len(results) >= limit:
                        break
    
    # Search Open WebUI operations
    for op_id, op_data in openwebui_tools.items():
        if (query_lower in op_id.lower() or 
            query_lower in op_data.get("description", "").lower()):
            results.append({
                "service": "openwebui",
                "operation_id": op_id,
                "description": op_data.get("description", ""),
                "method": op_data.get("method", "GET")
            })
            if len(results) >= limit:
                break
    
    return {
        "query": query,
        "results": results[:limit],
        "count": len(results[:limit])
    }

@mcp.resource("mcp://factory/stats")
def get_factory_stats() -> Dict[str, Any]:
    """Get current factory statistics."""
    google_operations = sum(
        sum(len(ops) for ops in service.values()) 
        for service in blueprints.values()
    )
    
    return {
        "google_cloud_services": len(blueprints),
        "google_cloud_operations": google_operations,
        "openwebui_operations": len(openwebui_tools),
        "total_operations": google_operations + len(openwebui_tools),
        "status": "operational"
    }

@mcp.resource("mcp://factory/health")
def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "blueprints_loaded": len(blueprints) > 0,
        "openwebui_tools_loaded": len(openwebui_tools) > 0,
        "timestamp": os.popen('date').read().strip()
    }

# Load blueprints on startup
load_blueprints()

if __name__ == "__main__":
    # Run the MCP server
    port = int(os.getenv("MCP_PORT", "8888"))
    host = os.getenv("MCP_HOST", "0.0.0.0")
    
    logger.info(f"Starting MCP Factory on {host}:{port}")
    uvicorn.run(mcp, host=host, port=port, log_level="info")
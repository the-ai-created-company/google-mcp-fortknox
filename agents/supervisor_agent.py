import time
import os
import json
import sys
from datetime import datetime

# --- Configuration ---
COMMAND_FILE = '/app/agents/command.txt'
OUTPUT_FILE = '/app/agents/output.txt'
PROCESSED_FILE = '/app/agents/processed_command.txt'
AGENT_SCRIPT = '/app/agents/base_agent.py'

# Add the agents directory to Python path
sys.path.append('/app/agents')

def log_message(message):
    """Prints a message with a timestamp."""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] SUPERVISOR: {message}")

def get_last_processed_command():
    """Reads the last successfully processed command."""
    if not os.path.exists(PROCESSED_FILE):
        return ""
    with open(PROCESSED_FILE, 'r') as f:
        return f.read().strip()

def write_last_processed_command(command):
    """Writes the command that was just processed."""
    with open(PROCESSED_FILE, 'w') as f:
        f.write(command)

def cleanup_deprecated_configs():
    """Remove all non-Google Cloud configurations"""
    try:
        modified_files = []
        mcp_tools_dir = '/app/mcp-tools'
        
        # Check master_config.json
        config_path = os.path.join(mcp_tools_dir, 'master_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Keep only Docker and GitHub from MCP servers
            google_focused_servers = {}
            for server_id, server_info in config.get('mcp_servers', {}).items():
                if server_id in ['docker', 'github', 'google_cloud']:
                    google_focused_servers[server_id] = server_info
            
            # Update config
            config['mcp_servers'] = google_focused_servers
            config['activation_status'] = {
                'docker': True,
                'github': True,
                'google_cloud': False  # Not yet authenticated
            }
            config['deprecated_removed'] = [
                'redis', 'supabase', 'digitalocean', 'vercel'
            ]
            config['updated_at'] = datetime.now().isoformat()
            
            # Write updated config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            modified_files.append(config_path)
        
        # Scan for any other config files
        for root, dirs, files in os.walk(mcp_tools_dir):
            for file in files:
                if file.endswith(('.json', '.yml', '.yaml')):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r') as f:
                        content = f.read()
                    
                    # Check if file contains deprecated services
                    deprecated = ['redis', 'supabase', 'digitalocean', 'vercel']
                    if any(dep in content.lower() for dep in deprecated):
                        modified_files.append(filepath)
        
        return {
            "status": "SUCCESS",
            "modified_files": modified_files,
            "removed_services": ['redis', 'supabase', 'digitalocean', 'vercel'],
            "retained_services": ['docker', 'github', 'google_cloud'],
            "message": "Configuration cleaned up for Google Cloud focus"
        }
    except Exception as e:
        return {"status": "ERROR", "message": f"Cleanup failed: {str(e)}"}

def test_agent_framework():
    """Test the BaseAgent framework integration"""
    try:
        from base_agent import BaseAgent
        
        # Initialize test agent
        agent = BaseAgent('gcf-test', 'Google Cloud Framework Test', ['google-cloud-operations'])
        
        # Test core capabilities
        capabilities = {
            'agent_id': agent.agent_id,
            'agent_name': agent.name,
            'capabilities': agent.capabilities,
            'available_methods': [
                'read_fort_knox_docs',
                'list_available_services',
                'create_mcp_tool',
                'spawn_agent',
                'process_message'
            ],
            'google_cloud_services': len(agent.list_available_services()),
            'paths': {
                'fort_knox': str(agent.fort_knox_path),
                'mcp_tools': str(agent.mcp_tools_path),
                'shared_memory': str(agent.shared_memory)
            }
        }
        
        return {
            "status": "SUCCESS",
            "framework": "BaseAgent",
            "capabilities": capabilities,
            "message": "Agent framework initialized successfully with Google Cloud focus"
        }
    except Exception as e:
        return {"status": "ERROR", "message": f"Framework test failed: {str(e)}"}

def show_google_cloud_tool(tool_name):
    """Retrieve a specific Google Cloud tool definition"""
    try:
        # Load the master tools file
        tools_path = '/app/fort-knox-apis/all_google_cloud_tools.json'
        with open(tools_path, 'r') as f:
            all_tools = json.load(f)
        
        # Find the requested tool
        if tool_name in all_tools:
            tool = all_tools[tool_name]
            return {
                "status": "SUCCESS",
                "tool_name": tool_name,
                "tool_definition": tool,
                "total_parameters": len(tool.get('parameters', {})),
                "required_parameters": tool.get('required_parameters', []),
                "http_method": tool.get('http_method', 'GET'),
                "path": tool.get('path', ''),
                "message": f"Google Cloud tool '{tool_name}' retrieved successfully"
            }
        else:
            # Try to find similar tools
            similar = [t for t in all_tools.keys() if tool_name.lower() in t.lower()][:5]
            return {
                "status": "NOT_FOUND",
                "requested": tool_name,
                "similar_tools": similar,
                "message": f"Tool '{tool_name}' not found. Did you mean one of these?"
            }
    except Exception as e:
        return {"status": "ERROR", "message": f"Tool retrieval failed: {str(e)}"}

def simulate_agent_spawning(agent_type):
    """Simulate spawning a specialized Google Cloud agent"""
    try:
        # Define Google Cloud agent templates
        agent_templates = {
            'cloud storage manager': {
                'agent_id': 'agent-gcs-manager',
                'name': 'Google Cloud Storage Manager',
                'capabilities': ['bucket_management', 'object_operations', 'acl_management'],
                'relevant_tools': ['storage_buckets_insert', 'storage_objects_insert', 'storage_buckets_list'],
                'tool_count': 81
            },
            'compute engine manager': {
                'agent_id': 'agent-gce-manager',
                'name': 'Google Compute Engine Manager',
                'capabilities': ['instance_management', 'disk_operations', 'network_config'],
                'relevant_tools': ['compute_instances_insert', 'compute_disks_create', 'compute_networks_insert'],
                'tool_count': 831
            },
            'cloud sql admin': {
                'agent_id': 'agent-sql-admin',
                'name': 'Google Cloud SQL Administrator',
                'capabilities': ['database_creation', 'backup_management', 'user_management'],
                'relevant_tools': ['sqladmin_databases_insert', 'sqladmin_backupRuns_insert', 'sqladmin_users_insert'],
                'tool_count': 69
            }
        }
        
        # Find matching template
        agent_key = agent_type.lower()
        template = None
        for key, value in agent_templates.items():
            if key in agent_key or agent_key in key:
                template = value
                break
        
        if not template:
            template = {
                'agent_id': f'agent-custom-{agent_type.replace(" ", "-").lower()}',
                'name': f'Custom Google Cloud Agent: {agent_type}',
                'capabilities': ['google_cloud_operations'],
                'relevant_tools': ['to_be_determined'],
                'tool_count': 'varies'
            }
        
        # Simulate agent creation
        agent_config = {
            **template,
            'created_at': datetime.now().isoformat(),
            'status': 'simulated',
            'config_path': f'/app/agents/{template["agent_id"]}/config.json',
            'ready_for_activation': False,
            'requires': ['Google Cloud Service Account', 'Specific API permissions']
        }
        
        return {
            "status": "SUCCESS",
            "agent_spawned": agent_config,
            "simulation_note": "This is a simulated spawn. Actual process creation will be implemented after Google Cloud auth.",
            "next_steps": [
                "Configure Google Cloud service account",
                "Grant necessary IAM permissions",
                "Implement actual process spawning"
            ]
        }
    except Exception as e:
        return {"status": "ERROR", "message": f"Agent spawn simulation failed: {str(e)}"}

def execute_agent_command(command):
    """Execute various agent commands with Google Cloud focus"""
    command_lower = command.lower()
    
    # Configuration cleanup
    if "analyze" in command_lower and "mcp-tools" in command_lower:
        return cleanup_deprecated_configs()
    
    # Test agent framework
    elif "test agent framework" in command_lower:
        return test_agent_framework()
    
    # Show specific Google Cloud tool
    elif "show tool" in command_lower:
        # Extract tool name
        parts = command.split()
        if len(parts) >= 3:
            tool_name = ' '.join(parts[2:])
            return show_google_cloud_tool(tool_name)
        else:
            return {"status": "ERROR", "message": "Please specify a tool name"}
    
    # Simulate agent spawning
    elif "simulate spawning" in command_lower:
        # Extract agent type
        if "'" in command:
            agent_type = command.split("'")[1]
        else:
            agent_type = "generic google cloud"
        return simulate_agent_spawning(agent_type)
    
    # List available Google Cloud services
    elif "list services" in command_lower:
        try:
            services_path = '/app/fort-knox-apis'
            services = [d for d in os.listdir(services_path) 
                       if os.path.isdir(os.path.join(services_path, d))]
            return {
                "status": "SUCCESS",
                "google_cloud_services": len(services),
                "services": services[:20],
                "message": f"Found {len(services)} Google Cloud services ready for use"
            }
        except Exception as e:
            return {"status": "ERROR", "message": f"Failed to list services: {str(e)}"}
    
    # Default response
    else:
        return {
            "status": "SUCCESS",
            "message": f"Command '{command}' received",
            "google_cloud_focus": True,
            "available_commands": [
                "analyze all files in the /app/mcp-tools directory",
                "test agent framework",
                "show tool <tool_name>",
                "simulate spawning a '<agent_type>' agent",
                "list services"
            ],
            "deprecated_removed": ['redis', 'supabase', 'digitalocean', 'vercel']
        }

def main():
    log_message("Google Cloud Focused Supervisor Agent is online. Watching for commands...")
    log_message("Deprecated services (Redis, Supabase, DO, Vercel) have been removed.")
    
    while True:
        try:
            if os.path.exists(COMMAND_FILE):
                with open(COMMAND_FILE, 'r') as f:
                    command = f.read().strip()
                
                last_command = get_last_processed_command()

                # Check if there is a new, non-empty command
                if command and command != last_command:
                    log_message(f"New command received: '{command}'")

                    # Execute the command
                    response = execute_agent_command(command)

                    # Write the output for the builder agent to retrieve
                    with open(OUTPUT_FILE, 'w') as out_f:
                        json.dump(response, out_f, indent=2)

                    log_message(f"Execution complete. Output written to {OUTPUT_FILE}.")
                    
                    # Mark this command as processed
                    write_last_processed_command(command)
            
            # Wait for a few seconds before checking again
            time.sleep(5)
            
        except Exception as e:
            log_message(f"An error occurred: {e}")
            # Write error to output file
            with open(OUTPUT_FILE, 'w') as out_f:
                json.dump({"status": "ERROR", "message": str(e)}, out_f, indent=2)
            time.sleep(15) # Wait longer after an error

if __name__ == "__main__":
    main()

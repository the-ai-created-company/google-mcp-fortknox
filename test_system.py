"""
Fort Knox System Overview & Integration Test
"""
import os
import json
import sys

print("Fort Knox System Overview")
print("=" * 50)

# Check what's available in the current directory
repo_path = r"C:\Users\Not John Or Justin\Desktop\google-mcp-fortknox"

# 1. Check Agents
print("\n[AGENTS AVAILABLE]:")
agents_path = os.path.join(repo_path, "agents")
if os.path.exists(agents_path):
    for agent in os.listdir(agents_path):
        agent_path = os.path.join(agents_path, agent)
        if os.path.isdir(agent_path):
            print(f"  + {agent}")
else:
    print("  - Agents directory not found")

# 2. Check Fort Knox APIs
print("\n[FORT KNOX APIs]:")
apis_path = os.path.join(repo_path, "fort-knox-apis")
if os.path.exists(apis_path):
    for api_file in os.listdir(apis_path):
        if api_file.endswith('.json'):
            print(f"  + {api_file}")
else:
    print("  - Fort Knox APIs directory not found")

# 3. Check MCP Tools
print("\n[MCP TOOLS]:")
mcp_tools_path = os.path.join(repo_path, "mcp-tools")
if os.path.exists(mcp_tools_path):
    for tool in os.listdir(mcp_tools_path):
        if tool.endswith('.py') or tool.endswith('.js'):
            print(f"  + {tool}")
else:
    print("  - MCP Tools directory not found")

# 4. Check Extracted Data (Google Cloud API Documentation)
print("\n[GOOGLE CLOUD API DOCUMENTATION]:")
extracted_path = os.path.join(repo_path, "extracted-data")
if os.path.exists(extracted_path):
    api_count = 0
    for api_dir in os.listdir(extracted_path):
        api_path = os.path.join(extracted_path, api_dir)
        if os.path.isdir(api_path):
            api_count += 1
    print(f"  + {api_count} Google Cloud APIs documented")
else:
    print("  - Extracted data directory not found")

# 5. Load and display master index
print("\n[MASTER INDEX]:")
master_index_path = os.path.join(repo_path, "master_index.json")
if os.path.exists(master_index_path):
    with open(master_index_path, 'r') as f:
        master_index = json.load(f)
        print(f"  + Google Cloud Operations: {master_index['google_cloud_services']['total_operations']}")
        print(f"  + OpenWebUI Operations: {master_index['openwebui_control']['total_operations']}")
        print(f"  + Total Available: {master_index['grand_total']['total_available']}")
        print(f"  + MCP Tools Built: {master_index['grand_total']['mcp_tools_built']}")
        print(f"  + Services Documented: {len(master_index['google_cloud_services']['services'])}")
else:
    print("  - Master index not found")

# 6. Check Base Agent
print("\n[BASE AGENT STRUCTURE]:")
base_agent_path = os.path.join(repo_path, "agents", "base_agent.py")
if os.path.exists(base_agent_path):
    print("  + base_agent.py found")
    # Read first few lines to understand structure
    with open(base_agent_path, 'r') as f:
        lines = f.readlines()[:20]
        print("\n  First 20 lines of base_agent.py:")
        for i, line in enumerate(lines, 1):
            print(f"    {i:2d}: {line.rstrip()}")
else:
    print("  - base_agent.py not found")

print("\n" + "=" * 50)
print("[!] System Overview Complete!")
print("\nThis Fort Knox system contains:")
print("- AI Agents that can modify themselves")
print("- 400+ Google Cloud API documentation")
print("- MCP tools for infrastructure management")
print("- Integration with Open WebUI")
print("\nThe agents can:")
print("1. Create new MCP tools dynamically")
print("2. Spawn other specialized agents")
print("3. Discover and integrate with APIs")
print("4. Manage Google Cloud infrastructure")
print("5. Communicate through shared memory")

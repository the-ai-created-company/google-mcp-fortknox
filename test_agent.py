#!/usr/bin/env python
"""Test if we can import and use the base agent"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from agents.base_agent import BaseAgent
    print("[OK] Successfully imported BaseAgent")
    
    # Try to instantiate the base agent with correct parameters
    agent = BaseAgent(
        agent_id="test-001",
        name="TestAgent",
        capabilities=["testing", "verification"]
    )
    print(f"[OK] Successfully created agent: {agent.name} (ID: {agent.agent_id})")
    
    # Test if we can access agent methods
    if hasattr(agent, 'process_message'):
        print("[OK] Agent has 'process_message' method")
        result = agent.process_message("Hello Test")
        print(f"[OK] process_message returned: {result}")
    
    if hasattr(agent, 'create_mcp_tool'):
        print("[OK] Agent has 'create_mcp_tool' method")
        
    if hasattr(agent, 'spawn_agent'):
        print("[OK] Agent has 'spawn_agent' method")
    
    # Test Fort Knox documentation access
    services = agent.list_available_services()
    print(f"[OK] Available Fort Knox services: {len(services)} found")
    
    # Test shared memory paths
    print(f"[OK] Shared memory path: {agent.shared_memory}")
    print(f"[OK] MCP tools path: {agent.mcp_tools_path}")
    
    print("\n[SUCCESS] Base agent system is working correctly!")
    
except ImportError as e:
    print(f"[ERROR] Failed to import BaseAgent: {e}")
except Exception as e:
    print(f"[ERROR] Error testing agent: {e}")
    import traceback
    traceback.print_exc()

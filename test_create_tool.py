#!/usr/bin/env python
"""Test creating an actual MCP tool using the agent framework"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from agents.base_agent import BaseAgent
    print("[OK] Successfully imported BaseAgent")
    
    # Create a test agent
    agent = BaseAgent(
        agent_id="test-creator-001",
        name="ToolCreatorTestAgent",
        capabilities=["tool-creation", "testing"]
    )
    print(f"[OK] Created agent: {agent.name}")
    
    # Create a simple MCP tool
    tool_code = '''import { z } from 'zod';

export const helloWorldTool = {
  name: 'hello_world',
  description: 'A simple test tool that returns a greeting',
  schema: z.object({
    name: z.string().describe('Name to greet')
  }),
  execute: async ({ name }) => {
    return {
      success: true,
      greeting: `Hello ${name}! This tool was created by an autonomous agent.`,
      timestamp: new Date().toISOString()
    };
  }
};
'''
    
    print("\n[ACTION] Creating MCP tool 'hello_world'...")
    result = agent.create_mcp_tool(
        tool_name="hello_world",
        tool_code=tool_code,
        category="test-tools"
    )
    print(f"[OK] Tool creation result: {result}")
    
    # Now let's verify the tool was created
    print("\n[ACTION] Checking if tool file exists...")
    tool_path = agent.mcp_tools_path / "test-tools" / "hello_world.ts"
    
    if tool_path.exists():
        print(f"[OK] Tool file created at: {tool_path}")
        
        # Read back the tool to verify
        with open(tool_path, 'r', encoding='utf-8') as f:
            saved_code = f.read()
        
        print(f"[OK] Tool file size: {len(saved_code)} bytes")
        print("[OK] Tool code successfully saved!")
        
        # Check the tool registry
        registry_path = agent.mcp_tools_path / "tool_registry.json"
        if registry_path.exists():
            import json
            with open(registry_path, 'r', encoding='utf-8') as f:
                registry = json.load(f)
            print(f"[OK] Tool registry updated: {registry}")
        else:
            print("[INFO] Tool registry not found (will be created on first tool)")
    else:
        print(f"[ERROR] Tool file not found at expected path: {tool_path}")
    
    print("\n[SUCCESS] MCP tool creation test completed!")
    
except Exception as e:
    print(f"[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()

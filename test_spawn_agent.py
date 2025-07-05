#!/usr/bin/env python
"""Test agent spawning capability"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from agents.base_agent import BaseAgent
    print("[OK] Successfully imported BaseAgent")
    
    # Create a test agent
    agent = BaseAgent(
        agent_id="test-spawner-001",
        name="AgentSpawner",
        capabilities=["agent-creation", "testing"]
    )
    print(f"[OK] Created agent: {agent.name}")
    
    # Spawn a new specialized agent
    print("\n[ACTION] Spawning a new Database Admin agent...")
    result = agent.spawn_agent(
        agent_type="database-specialist",
        agent_config={
            "capabilities": ["database-management", "sql-optimization", "backup-restore"],
            "databases": ["PostgreSQL", "Cloud SQL", "Redis"],
            "auto_start": True
        }
    )
    print(f"[OK] Agent spawn result: {result}")
    
    # Check if the new agent directory was created
    agents_path = agent.agents_path
    print(f"\n[ACTION] Checking agents directory: {agents_path}")
    
    # List all agent directories
    import os
    if os.path.exists(agents_path):
        agent_dirs = [d for d in os.listdir(agents_path) if os.path.isdir(os.path.join(agents_path, d)) and d.startswith("agent-")]
        print(f"[OK] Found {len(agent_dirs)} agents:")
        for agent_dir in sorted(agent_dirs):
            print(f"  - {agent_dir}")
    
    print("\n[SUCCESS] Agent spawning test completed!")
    
except Exception as e:
    print(f"[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()

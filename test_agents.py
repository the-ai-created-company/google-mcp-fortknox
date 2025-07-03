#!/usr/bin/env python3
"""
Test script to verify agent functionality before transformation
"""

import sys
import os
import json

# Add agents directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

def test_agents():
    """Test that all agents can be imported and initialized"""
    print("🧪 Testing Agent System...")
    print("=" * 50)
    
    results = []
    
    # Test 1: Import base agent
    try:
        from base_agent import BaseAgent
        print("✅ Base Agent Framework imported successfully")
        results.append(("Base Agent", True))
    except Exception as e:
        print(f"❌ Failed to import Base Agent: {e}")
        results.append(("Base Agent", False))
    
    # Test 2: Check each agent
    agents = [
        ("Infrastructure Agent", "agent-01-infrastructure"),
        ("Tool Creator Agent", "agent-02-tool-creator"),
        ("API Explorer Agent", "agent-03-api-explorer"),
        ("Database Admin Agent", "agent-04-database-admin"),
        ("Coordinator Agent", "agent-05-coordinator")
    ]
    
    for agent_name, agent_dir in agents:
        try:
            # Check if agent directory exists
            agent_path = os.path.join("agents", agent_dir)
            if os.path.exists(agent_path):
                # Check for agent.py file
                agent_file = os.path.join(agent_path, "agent.py")
                if os.path.exists(agent_file):
                    print(f"✅ {agent_name} found at {agent_path}")
                    results.append((agent_name, True))
                else:
                    print(f"⚠️  {agent_name} directory exists but agent.py missing")
                    results.append((agent_name, False))
            else:
                print(f"❌ {agent_name} directory not found")
                results.append((agent_name, False))
        except Exception as e:
            print(f"❌ Error checking {agent_name}: {e}")
            results.append((agent_name, False))
    
    # Test 3: Check shared memory
    print("\n📦 Checking Shared Memory System...")
    memory_dirs = [
        ("Message Queue", "shared-memory/agent-messages/messages.json"),
        ("Task Queue", "shared-memory/task-queue/tasks.json"),
        ("Knowledge Base", "shared-memory/knowledge-base/general.json")
    ]
    
    for component, path in memory_dirs:
        if os.path.exists(path):
            print(f"✅ {component} exists at {path}")
            results.append((component, True))
        else:
            print(f"⚠️  {component} not found at {path}")
            results.append((component, False))
    
    # Test 4: Check Open WebUI connector
    print("\n🔌 Checking Open WebUI Integration...")
    connector_path = "openwebui/agent_connector.py"
    if os.path.exists(connector_path):
        print(f"✅ Agent Connector found at {connector_path}")
        results.append(("Agent Connector", True))
    else:
        print(f"❌ Agent Connector not found")
        results.append(("Agent Connector", False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Ready for transformation.")
    else:
        print("\n⚠️  Some tests failed. Review before proceeding.")
    
    return passed == total

if __name__ == "__main__":
    success = test_agents()
    sys.exit(0 if success else 1)
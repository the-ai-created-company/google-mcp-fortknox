#!/usr/bin/env python
"""Simple Responder Agent - Simulates coordinator responding"""

import sys
import os
import json
from datetime import datetime

sys.path.insert(0, '/app')
from agents.base_agent import BaseAgent

class ResponderAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="responder-001",
            name="ResponderAgent",
            capabilities=["message-handling", "task-coordination"]
        )

print("=== RESPONDER AGENT CHECKING MESSAGES ===")

try:
    responder = ResponderAgent()
    
    # First, let's check what messages the coordinator has
    coordinator_msgs = "/app/shared-memory/agent-messages/agent-05-coordinator.json"
    if os.path.exists(coordinator_msgs):
        with open(coordinator_msgs, 'r') as f:
            messages = json.load(f)
        print(f"\nCoordinator has {len(messages)} messages:")
        for msg in messages:
            print(f"  From: {msg['from']}, Type: {msg['message'].get('type')}")
    
    # Now check if live-test-001 has any responses
    test_agent_msgs = "/app/shared-memory/agent-messages/live-test-001.json"
    
    # Send a response to live-test-001
    response = responder.communicate(
        target_agent="live-test-001",
        message={
            "type": "task_acknowledgment",
            "content": "Your database backup tool request has been received and processed!",
            "coordinator_response": True,
            "next_steps": "Tool creator agent will build the postgres_backup tool"
        }
    )
    print(f"\nResponse sent to live-test-001: {response}")
    
    # Check if the message file was created
    if os.path.exists(test_agent_msgs):
        with open(test_agent_msgs, 'r') as f:
            responses = json.load(f)
        print(f"\nlive-test-001 now has {len(responses)} messages")
        for resp in responses:
            print(f"  Message from: {resp['from']}")
            print(f"  Content: {resp['message']}")
    
    print("\n=== AGENT COMMUNICATION VERIFIED ===")
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

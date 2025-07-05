#!/usr/bin/env python
"""Coordinator Agent Response Test - This will check messages and respond"""

import sys
import os
import json
import time
from datetime import datetime

sys.path.insert(0, '/app')

# Import the actual coordinator agent
from agents.agent_05_coordinator.agent import CoordinatorAgent

# Run the coordinator to check messages
print("=== COORDINATOR AGENT RESPONDING TO MESSAGES ===")

try:
    coordinator = CoordinatorAgent()
    print(f"[{datetime.now()}] Coordinator Agent initialized")
    
    # Check for messages
    messages = coordinator.read_messages()
    print(f"\n[{datetime.now()}] Found {len(messages)} messages")
    
    for msg in messages:
        print(f"\nProcessing message from: {msg['from']}")
        print(f"Content: {msg['message']}")
        
        # Process the message
        if msg['message'].get('type') == 'task_request':
            print(f"This is a task request with priority: {msg['message'].get('priority')}")
            
            # Respond back
            response_sent = coordinator.communicate(
                target_agent=msg['from'],
                message={
                    "type": "task_acknowledgment",
                    "original_request": msg['message']['content'],
                    "response": "I've received your request for a database backup tool. Assigning to tool creator agent.",
                    "action_taken": "Created task for agent-02-tool-creator"
                }
            )
            print(f"Response sent: {response_sent}")
            
    # Check task queue
    print(f"\n[{datetime.now()}] Checking task queue...")
    tasks = coordinator.get_pending_tasks()
    print(f"Found {len(tasks)} pending tasks")
    
    # Check if tool creator should handle any tasks
    for task in tasks:
        if task.get('assigned_to') == 'agent-02-tool-creator' and task.get('status') == 'in_progress':
            print(f"\nTask {task['task_id']} is assigned to tool creator")
            print("In a real scenario, agent-02 would now create the requested tool")
    
    print(f"\n[{datetime.now()}] === COORDINATOR RESPONSE COMPLETE ===")
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

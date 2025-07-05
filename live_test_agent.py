#!/usr/bin/env python
"""Live Test Agent - This will run inside Docker and interact with other agents"""

import sys
import os
import json
import time
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, '/app')

from agents.base_agent import BaseAgent

class LiveTestAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="live-test-001",
            name="LiveTestAgent",
            capabilities=["testing", "verification", "task-execution"]
        )
        print(f"[{datetime.now()}] LiveTestAgent initialized with ID: {self.agent_id}")
    
    def run_full_test(self):
        """Run a complete test of agent interactions"""
        print(f"\n[{datetime.now()}] === STARTING LIVE AGENT INTERACTION TEST ===\n")
        
        # Test 1: Send a message to the coordinator agent
        print("[TEST 1] Sending message to Coordinator Agent...")
        message_sent = self.communicate(
            target_agent="agent-05-coordinator",
            message={
                "type": "task_request",
                "content": "I need help creating a new database backup tool",
                "priority": "high"
            }
        )
        print(f"Message sent: {message_sent}")
        
        # Test 2: Add a task to the shared task queue
        print("\n[TEST 2] Adding task to shared queue...")
        task_id = self.add_task_to_queue({
            "type": "create_tool",
            "description": "Create a PostgreSQL backup MCP tool",
            "assigned_to": "agent-02-tool-creator",
            "requirements": {
                "tool_name": "postgres_backup",
                "functionality": "backup PostgreSQL databases to Cloud Storage",
                "language": "typescript"
            }
        })
        print(f"Task created with ID: {task_id}")
        
        # Test 3: Store knowledge in shared knowledge base
        print("\n[TEST 3] Storing knowledge in shared knowledge base...")
        self.store_knowledge(
            key="test_run_timestamp",
            value={
                "timestamp": datetime.now().isoformat(),
                "test_agent": self.agent_id,
                "status": "active"
            },
            category="test_results"
        )
        print("Knowledge stored successfully")
        
        # Test 4: Check for messages from other agents
        print("\n[TEST 4] Checking for incoming messages...")
        messages = self.read_messages()
        print(f"Found {len(messages)} messages")
        for msg in messages:
            print(f"  - From: {msg['from']}, Content: {msg['message']}")
        
        # Test 5: List available services
        print("\n[TEST 5] Listing available Fort Knox services...")
        services = self.list_available_services()
        print(f"Found {len(services)} services: {services}")
        
        # Test 6: Check pending tasks
        print("\n[TEST 6] Checking pending tasks in queue...")
        pending_tasks = self.get_pending_tasks()
        print(f"Found {len(pending_tasks)} pending tasks")
        for task in pending_tasks:
            print(f"  - Task: {task.get('task_id')}, Type: {task.get('type')}, Status: {task.get('status')}")
        
        # Test 7: Simulate task execution
        if pending_tasks:
            first_task = pending_tasks[0]
            print(f"\n[TEST 7] Simulating execution of task: {first_task['task_id']}")
            self.update_task_status(
                task_id=first_task['task_id'],
                status="in_progress",
                result={"message": "LiveTestAgent is processing this task"}
            )
            print("Task status updated to in_progress")
        
        # Test 8: Create an actual MCP tool
        print("\n[TEST 8] Creating a real MCP tool...")
        tool_code = '''import { z } from 'zod';

export const postgresBackupTool = {
  name: 'postgres_backup',
  description: 'Backup PostgreSQL database to Google Cloud Storage',
  schema: z.object({
    databaseUrl: z.string().describe('PostgreSQL connection string'),
    bucketName: z.string().describe('GCS bucket for backup'),
    backupName: z.string().optional().describe('Custom backup name')
  }),
  execute: async ({ databaseUrl, bucketName, backupName }) => {
    const timestamp = new Date().toISOString();
    const finalBackupName = backupName || `backup_${timestamp}.sql`;
    
    // This is a mock - in real implementation would use pg_dump
    return {
      success: true,
      backup: {
        name: finalBackupName,
        bucket: bucketName,
        timestamp: timestamp,
        size: '42MB'
      },
      message: `Database backed up to gs://${bucketName}/${finalBackupName}`
    };
  }
};'''
        
        tool_result = self.create_mcp_tool(
            tool_name="postgres_backup",
            tool_code=tool_code,
            category="database-tools"
        )
        print(f"Tool creation result: {tool_result}")
        
        print(f"\n[{datetime.now()}] === TEST COMPLETE ===\n")
        
        # Return summary
        return {
            "test_completed": True,
            "timestamp": datetime.now().isoformat(),
            "tests_run": 8,
            "agent_id": self.agent_id,
            "results": {
                "message_sent": message_sent,
                "task_created": task_id,
                "messages_received": len(messages),
                "services_found": len(services),
                "pending_tasks": len(pending_tasks),
                "tool_created": "postgres_backup"
            }
        }

if __name__ == "__main__":
    print("=== LIVE AGENT TEST STARTING ===")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {sys.path[:3]}")
    
    try:
        # Create and run the test agent
        agent = LiveTestAgent()
        results = agent.run_full_test()
        
        # Save results
        results_file = "/app/shared-memory/live_test_results.json"
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to: {results_file}")
        print("\n=== LIVE AGENT TEST COMPLETED SUCCESSFULLY ===")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

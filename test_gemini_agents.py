"""Test script for Gemini-enhanced agents"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.agent_01_infrastructure.enhanced_agent import EnhancedInfrastructureAgent


async def test_gemini_integration():
    """Test the Gemini API integration"""
    print("=== Testing Gemini-Enhanced Infrastructure Agent ===\n")
    
    async with EnhancedInfrastructureAgent() as agent:
        # Test 1: Basic Gemini thinking
        print("Test 1: Basic AI Thinking")
        print("-" * 50)
        response = await agent.think_with_gemini(
            "What are the top 3 most important Google Cloud services for a startup?"
        )
        print(f"AI Response: {response}\n")
        
        # Test 2: Analyze available services
        print("Test 2: AI Infrastructure Analysis")
        print("-" * 50)
        services = agent.list_available_services()
        print(f"Available services: {services[:5]}...")
        
        # Test 3: Generate an MCP tool
        print("\nTest 3: AI Tool Generation")
        print("-" * 50)
        tool_spec = {
            "name": "smart_instance_manager",
            "description": "AI-powered Compute Engine instance manager",
            "category": "compute",
            "parameters": {
                "action": {"type": "string", "enum": ["create", "delete", "resize", "optimize"]},
                "instance_name": {"type": "string"},
                "zone": {"type": "string"}
            }
        }
        
        result = await agent.generate_mcp_tool(tool_spec)
        print(f"Tool generation result: {result}\n")
        
        # Test 4: Self-improvement analysis
        print("Test 4: Self-Improvement Analysis")
        print("-" * 50)
        improvement = await agent.self_improve()
        print(f"Self-improvement result: {improvement}\n")
        
        # Test 5: Handle a complex message
        print("Test 5: Complex Message Handling")
        print("-" * 50)
        message = {
            "text": "I need to set up a highly available web application that can handle 50,000 concurrent users with automatic scaling and disaster recovery"
        }
        response = await agent.handle_message(message)
        print(f"Agent response: {response[:500]}...\n")


async def test_multi_agent_communication():
    """Test communication between agents"""
    print("\n=== Testing Multi-Agent Communication ===\n")
    
    async with EnhancedInfrastructureAgent() as infra_agent:
        # Create a task for another agent
        task = {
            "type": "analyze_infrastructure",
            "priority": "high",
            "requirements": {
                "services": ["compute", "storage", "networking"],
                "focus": "security hardening"
            }
        }
        
        task_id = infra_agent.add_task_to_queue(task)
        print(f"Created task: {task_id}")
        
        # Send a message to another agent
        infra_agent.communicate(
            "agent-02-tool-creator",
            {
                "type": "tool_request",
                "message": "Please create a tool for automated security scanning",
                "priority": "medium"
            }
        )
        print("Sent message to tool creator agent")
        
        # Store knowledge
        infra_agent.store_knowledge(
            "gemini_test_results",
            {
                "api_working": True,
                "model": "gemini-2.0-flash-exp",
                "capabilities_tested": ["thinking", "analysis", "generation"]
            },
            category="test_results"
        )
        print("Stored test results in knowledge base")


async def main():
    """Run all tests"""
    try:
        # Test Gemini integration
        await test_gemini_integration()
        
        # Test multi-agent features
        await test_multi_agent_communication()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Starting Gemini Agent Tests...")
    print(f"Using Gemini model: gemini-2.0-flash-exp")
    print("=" * 60 + "\n")
    
    asyncio.run(main())

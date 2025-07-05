"""Enhanced Infrastructure Management Agent with Gemini AI

This agent specializes in managing Google Cloud infrastructure by:
- Using Gemini AI to analyze and optimize infrastructure
- Reading Fort Knox documentation to understand available services
- Creating and configuring cloud resources intelligently
- Monitoring infrastructure health with AI-driven insights
- Scaling services based on demand predictions
- Creating MCP tools for infrastructure automation
"""

from pathlib import Path
import sys
import asyncio
import json
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.enhanced_base_agent import EnhancedBaseAgent


class EnhancedInfrastructureAgent(EnhancedBaseAgent):
    """AI-powered agent specialized in Google Cloud infrastructure management"""
    
    def __init__(self):
        super().__init__(
            agent_id="agent-01-infrastructure",
            name="AI Infrastructure Manager",
            capabilities=[
                "ai_infrastructure_analysis",
                "intelligent_resource_creation",
                "predictive_scaling",
                "automated_optimization",
                "security_hardening",
                "cost_optimization_ai",
                "self_healing_infrastructure",
                "mcp_tool_generation"
            ]
        )
        self.supported_services = [
            "compute", "storage", "run", "sql", "redis",
            "bigquery", "pubsub", "vpc", "loadbalancing",
            "container", "functions", "firestore", "spanner"
        ]
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process infrastructure tasks with AI assistance"""
        task_type = task.get("type", "")
        
        try:
            if task_type == "analyze_infrastructure":
                result = await self.ai_analyze_infrastructure()
                return {"status": "completed", "result": result}
            
            elif task_type == "optimize_costs":
                result = await self.ai_optimize_costs()
                return {"status": "completed", "result": result}
            
            elif task_type == "create_architecture":
                requirements = task.get("requirements", {})
                result = await self.design_architecture(requirements)
                return {"status": "completed", "result": result}
            
            elif task_type == "generate_tool":
                service = task.get("service", "")
                operation = task.get("operation", "")
                result = await self.ai_create_infrastructure_tool(service, operation)
                return {"status": "completed", "result": result}
            
            elif task_type == "predict_scaling":
                result = await self.predict_scaling_needs()
                return {"status": "completed", "result": result}
            
            else:
                # Use AI to understand and handle unknown tasks
                result = await self.ai_handle_unknown_task(task)
                return {"status": "completed", "result": result}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def handle_message(self, message: Dict[str, Any]) -> str:
        """Handle incoming messages with AI understanding"""
        message_text = message.get("text", "")
        
        # Use Gemini to understand the intent
        intent_prompt = f"""Analyze this message and determine the user's intent regarding infrastructure management:

Message: {message_text}

Possible intents:
1. analyze_infrastructure - User wants analysis of current infrastructure
2. create_resource - User wants to create a new resource
3. optimize_costs - User wants cost optimization
4. scale_service - User wants to scale a service
5. generate_tool - User wants to create an MCP tool
6. design_architecture - User wants architecture recommendations
7. troubleshoot - User has an infrastructure issue
8. general_question - General infrastructure question

Return the intent and any extracted parameters as JSON.
"""
        
        response = await self.think_with_gemini(intent_prompt)
        
        try:
            intent_data = json.loads(response)
            intent = intent_data.get("intent", "general_question")
            params = intent_data.get("parameters", {})
        except:
            # Fallback to general response
            return await self.think_with_gemini(f"Respond to this infrastructure-related message: {message_text}")
        
        # Handle based on intent
        if intent == "analyze_infrastructure":
            analysis = await self.ai_analyze_infrastructure()
            return f"Infrastructure Analysis:\n{json.dumps(analysis, indent=2)}"
        
        elif intent == "generate_tool":
            service = params.get("service", "compute")
            operation = params.get("operation", "list")
            result = await self.ai_create_infrastructure_tool(service, operation)
            return result
        
        else:
            # Use AI for general response
            return await self.think_with_gemini(message_text, {"role": "infrastructure_manager"})
    
    async def ai_analyze_infrastructure(self) -> Dict[str, Any]:
        """Use AI to analyze infrastructure needs and opportunities"""
        # First, gather available documentation
        available_services = self.list_available_services()
        
        # Analyze each service's documentation
        service_analysis = {}
        for service in available_services[:5]:  # Limit to 5 for demo
            docs = self.read_fort_knox_docs(service)
            if docs:
                analysis_prompt = f"""Analyze this Google Cloud {service} documentation and provide:
1. Most useful operations for automation
2. Common use cases
3. Security considerations
4. Cost optimization opportunities
5. Recommended MCP tools to create

Documentation summary:
- Endpoints: {len(docs.get('api_endpoints', {}))}
- Resources: {list(docs.get('resource_types', {}).keys())[:10]}

Provide a concise analysis.
"""
                
                analysis = await self.think_with_gemini(analysis_prompt)
                service_analysis[service] = analysis
        
        # Overall infrastructure recommendations
        overall_prompt = f"""Based on the available Google Cloud services: {available_services}

Provide infrastructure recommendations for:
1. Essential services to set up first
2. Security baseline configuration
3. Cost optimization strategy
4. Monitoring and alerting setup
5. Disaster recovery planning

Format as actionable recommendations.
"""
        
        overall_recommendations = await self.think_with_gemini(overall_prompt)
        
        return {
            "available_services": available_services,
            "service_analysis": service_analysis,
            "recommendations": overall_recommendations,
            "next_steps": [
                "Create essential MCP tools",
                "Set up monitoring",
                "Configure security policies",
                "Implement cost controls"
            ]
        }
    
    async def ai_create_infrastructure_tool(self, service: str, operation: str) -> str:
        """Use AI to create sophisticated infrastructure tools"""
        # Read the documentation
        docs = self.read_fort_knox_docs(service)
        if not docs:
            # Ask AI to suggest what to do
            suggestion = await self.think_with_gemini(
                f"No documentation found for {service}. Suggest how to create an MCP tool for {operation} operation."
            )
            return suggestion
        
        # Use AI to design the tool
        tool_spec = await self.analyze_google_cloud_api(service)
        
        # Generate the tool
        tool_name = f"{service}_{operation}_intelligent"
        tool_config = {
            "name": tool_name,
            "description": f"AI-enhanced tool for {service} {operation} operations",
            "category": "infrastructure",
            "parameters": {
                "project_id": {"type": "string", "description": "Google Cloud project ID"},
                "region": {"type": "string", "description": "Region for the operation"},
                "config": {"type": "object", "description": "Operation-specific configuration"}
            }
        }
        
        result = await self.generate_mcp_tool(tool_config)
        
        # Create an enhanced version with AI capabilities
        enhanced_code = await self.enhance_tool_with_ai(tool_name)
        
        return f"Created AI-enhanced tool: {tool_name}\n{result}"
    
    async def enhance_tool_with_ai(self, tool_name: str) -> str:
        """Enhance an MCP tool with AI capabilities"""
        enhancement_prompt = f"""Enhance the {tool_name} MCP tool with these AI capabilities:

1. Intelligent parameter validation
2. Automatic error recovery
3. Performance optimization
4. Cost estimation before execution
5. Security vulnerability checking
6. Automated documentation generation

Generate code snippets for these enhancements.
"""
        
        enhancements = await self.think_with_gemini(enhancement_prompt)
        
        # Save enhancements
        enhancement_path = self.mcp_tools_path / "enhancements" / f"{tool_name}_ai.ts"
        enhancement_path.parent.mkdir(parents=True, exist_ok=True)
        enhancement_path.write_text(enhancements, encoding='utf-8')
        
        return f"AI enhancements saved to {enhancement_path}"
    
    async def design_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to design infrastructure architecture"""
        design_prompt = f"""Design a Google Cloud infrastructure architecture based on these requirements:

{json.dumps(requirements, indent=2)}

Consider:
1. Scalability and performance
2. Security best practices
3. Cost optimization
4. High availability
5. Disaster recovery
6. Monitoring and observability

Provide:
1. Architecture diagram description
2. Service selection and justification
3. Network topology
4. Security measures
5. Estimated costs
6. Implementation roadmap
"""
        
        architecture = await self.think_with_gemini(design_prompt)
        
        # Generate Terraform code
        terraform_prompt = f"""Based on this architecture design, generate Terraform code to implement it:

{architecture}

Include:
1. Resource definitions
2. Network configuration
3. Security policies
4. Monitoring setup
5. Variables and outputs
"""
        
        terraform_code = await self.think_with_gemini(terraform_prompt)
        
        # Save the design
        design_path = self.shared_memory / "architectures" / f"design_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        design_path.parent.mkdir(parents=True, exist_ok=True)
        
        design_data = {
            "requirements": requirements,
            "architecture": architecture,
            "terraform": terraform_code,
            "created_by": self.agent_id,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(design_path, 'w', encoding='utf-8') as f:
            json.dump(design_data, f, indent=2)
        
        return {
            "design": architecture,
            "terraform_path": str(design_path),
            "next_steps": [
                "Review and approve design",
                "Customize Terraform code",
                "Plan deployment",
                "Set up CI/CD"
            ]
        }
    
    async def predict_scaling_needs(self) -> Dict[str, Any]:
        """Use AI to predict infrastructure scaling needs"""
        prediction_prompt = """Based on common patterns, predict infrastructure scaling needs for:

1. Daily traffic patterns
2. Weekly business cycles
3. Seasonal variations
4. Growth projections
5. Special events

Provide specific recommendations for:
- Compute Engine autoscaling
- Cloud Run scaling
- Database connection pooling
- Storage capacity planning
- Network bandwidth

Include proactive measures to handle predicted load.
"""
        
        predictions = await self.think_with_gemini(prediction_prompt)
        
        # Generate scaling policies
        policies_prompt = f"""Based on these scaling predictions, generate specific autoscaling policies:

{predictions}

Format as JSON configuration for:
1. Compute Engine instance groups
2. Cloud Run services
3. Cloud SQL read replicas
4. Memorystore Redis clusters
"""
        
        scaling_policies = await self.think_with_gemini(policies_prompt)
        
        return {
            "predictions": predictions,
            "scaling_policies": scaling_policies,
            "implementation_priority": [
                "Configure Cloud Run autoscaling",
                "Set up Compute Engine managed instance groups",
                "Implement database read replicas",
                "Configure CDN and caching"
            ]
        }
    
    async def ai_optimize_costs(self) -> Dict[str, Any]:
        """Use AI to optimize infrastructure costs"""
        optimization_prompt = """Analyze typical Google Cloud infrastructure patterns and suggest cost optimizations:

1. Resource rightsizing recommendations
2. Committed use discount opportunities  
3. Preemptible/Spot instance usage
4. Storage class optimization
5. Network egress reduction
6. Idle resource identification
7. Service consolidation opportunities

Provide specific, actionable recommendations with estimated savings.
"""
        
        optimizations = await self.think_with_gemini(optimization_prompt)
        
        # Generate implementation scripts
        scripts_prompt = f"""Generate scripts to implement these cost optimizations:

{optimizations}

Include:
1. Resource analysis scripts
2. Automated rightsizing
3. Storage lifecycle policies
4. Cleanup automation
5. Cost alerting setup
"""
        
        implementation_scripts = await self.think_with_gemini(scripts_prompt)
        
        # Save optimization plan
        plan_path = self.shared_memory / "cost_optimization" / f"plan_{datetime.now().strftime('%Y%m%d')}.json"
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        
        optimization_plan = {
            "analysis": optimizations,
            "scripts": implementation_scripts,
            "estimated_savings": "20-40% based on typical patterns",
            "created_by": self.agent_id,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(plan_path, 'w', encoding='utf-8') as f:
            json.dump(optimization_plan, f, indent=2)
        
        return optimization_plan
    
    async def ai_handle_unknown_task(self, task: Dict[str, Any]) -> str:
        """Use AI to handle tasks not explicitly programmed"""
        creative_prompt = f"""You are an intelligent infrastructure management agent. 
You received this task that doesn't match any predefined handlers:

{json.dumps(task, indent=2)}

Use your knowledge of Google Cloud infrastructure to:
1. Understand what the user wants
2. Determine the best approach
3. Provide a helpful response or solution
4. Suggest any tools that should be created

Be creative and helpful!
"""
        
        response = await self.think_with_gemini(creative_prompt)
        
        # Check if we should create a new handler for this task type
        learning_prompt = f"""Based on this unknown task and response:
Task: {task.get('type', 'unknown')}
Response approach: {response[:200]}...

Should we create a new task handler for this? If yes, provide the handler code structure.
"""
        
        learning_response = await self.think_with_gemini(learning_prompt)
        
        # Self-improvement based on new task types
        if "yes" in learning_response.lower():
            await self.self_improve()
        
        return response


# Agent initialization
async def main():
    """Initialize and demonstrate the enhanced infrastructure agent"""
    async with EnhancedInfrastructureAgent() as agent:
        print(f"Enhanced Infrastructure Agent initialized: {agent.agent_id}")
        print(f"AI Capabilities: {agent.capabilities}")
        
        # Example: Analyze infrastructure
        print("\nAnalyzing infrastructure with AI...")
        analysis = await agent.ai_analyze_infrastructure()
        print(f"Found {len(analysis['available_services'])} services")
        
        # Example: Create an intelligent tool
        print("\nCreating AI-enhanced tool...")
        result = await agent.ai_create_infrastructure_tool("compute", "optimize_instances")
        print(result)
        
        # Example: Design architecture
        print("\nDesigning architecture...")
        requirements = {
            "application": "E-commerce platform",
            "expected_users": "100,000 daily",
            "regions": ["us-central1", "europe-west1"],
            "requirements": ["high availability", "PCI compliance", "auto-scaling"]
        }
        design = await agent.design_architecture(requirements)
        print(f"Architecture design saved to: {design['terraform_path']}")


if __name__ == "__main__":
    asyncio.run(main())

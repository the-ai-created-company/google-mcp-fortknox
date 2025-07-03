"""Coordinator Agent

This agent specializes in orchestrating other agents by:
- Managing task distribution across agents
- Monitoring agent health and performance
- Handling inter-agent communication
- Optimizing resource allocation
- Creating workflows and pipelines
- Resolving conflicts between agents
"""

from pathlib import Path
import sys
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import asyncio
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base_agent import BaseAgent


class CoordinatorAgent(BaseAgent):
    """Agent specialized in orchestrating and coordinating other agents"""
    
    def __init__(self):
        super().__init__(
            agent_id="agent-05-coordinator",
            name="Coordinator",
            capabilities=[
                "orchestrate_agents",
                "distribute_tasks",
                "monitor_agents",
                "create_workflows",
                "manage_pipelines",
                "resolve_conflicts",
                "optimize_allocation",
                "track_progress",
                "handle_failures",
                "scale_agents"
            ]
        )
        self.agent_registry = {}
        self.active_workflows = {}
        self.task_history = []
        self.performance_metrics = defaultdict(dict)
        self._discover_agents()
    
    def _discover_agents(self):
        """Discover all available agents in the repository"""
        agents_path = self.repo_root / "agents"
        
        for agent_dir in agents_path.iterdir():
            if agent_dir.is_dir() and agent_dir.name.startswith("agent-") and agent_dir.name != self.agent_id:
                # Check if agent is implemented
                agent_file = agent_dir / "agent.py"
                if agent_file.exists():
                    agent_info = {
                        "id": agent_dir.name,
                        "status": "available",
                        "capabilities": self._extract_agent_capabilities(agent_dir.name),
                        "current_tasks": [],
                        "performance": {
                            "tasks_completed": 0,
                            "tasks_failed": 0,
                            "average_completion_time": 0,
                            "reliability_score": 1.0
                        }
                    }
                    self.agent_registry[agent_dir.name] = agent_info
        
        # Store agent registry in knowledge base
        self.store_knowledge("agent_registry", self.agent_registry, category="coordination")
    
    def _extract_agent_capabilities(self, agent_id: str) -> List[str]:
        """Extract capabilities from agent ID and known patterns"""
        capability_map = {
            "infrastructure": ["create_resources", "scale_services", "monitor_health"],
            "tool-creator": ["analyze_api_docs", "generate_tool_code", "create_mcp_tools"],
            "api-explorer": ["discover_api", "generate_api_wrapper", "test_endpoints"],
            "database-admin": ["create_database", "execute_query", "backup_database"]
        }
        
        for key, capabilities in capability_map.items():
            if key in agent_id:
                return capabilities
        
        return ["general_task_execution"]
    
    def create_workflow(self, workflow_name: str, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a workflow that orchestrates multiple agents"""
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{workflow_name}"
        
        # Analyze tasks and assign to agents
        task_assignments = []
        for task in tasks:
            best_agent = self._find_best_agent_for_task(task)
            if best_agent:
                task_assignments.append({
                    "task": task,
                    "assigned_to": best_agent,
                    "status": "pending",
                    "dependencies": task.get("dependencies", [])
                })
            else:
                task_assignments.append({
                    "task": task,
                    "assigned_to": None,
                    "status": "unassigned",
                    "reason": "No suitable agent found"
                })
        
        # Create workflow
        workflow = {
            "id": workflow_id,
            "name": workflow_name,
            "created_at": datetime.now().isoformat(),
            "created_by": self.agent_id,
            "tasks": task_assignments,
            "status": "created",
            "progress": 0
        }
        
        self.active_workflows[workflow_id] = workflow
        
        # Store workflow in knowledge base
        self.store_knowledge(f"workflow_{workflow_id}", workflow, category="workflows")
        
        return workflow
    
    def _find_best_agent_for_task(self, task: Dict[str, Any]) -> Optional[str]:
        """Find the best agent to handle a specific task"""
        task_type = task.get("type", "")
        required_capabilities = task.get("required_capabilities", [])
        
        best_agent = None
        best_score = 0
        
        for agent_id, agent_info in self.agent_registry.items():
            # Calculate suitability score
            score = 0
            
            # Check task type match
            if task_type in agent_id:
                score += 5
            
            # Check capability match
            agent_capabilities = set(agent_info["capabilities"])
            required_set = set(required_capabilities)
            if required_set.issubset(agent_capabilities):
                score += 10
            else:
                # Partial match
                score += len(required_set.intersection(agent_capabilities)) * 2
            
            # Consider agent performance
            performance = agent_info["performance"]
            score *= performance["reliability_score"]
            
            # Consider current workload
            current_tasks = len(agent_info["current_tasks"])
            if current_tasks > 0:
                score = score / (1 + current_tasks * 0.2)  # Reduce score for busy agents
            
            if score > best_score:
                best_score = score
                best_agent = agent_id
        
        return best_agent
    
    def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a workflow by coordinating agents"""
        if workflow_id not in self.active_workflows:
            return {"success": False, "error": f"Workflow {workflow_id} not found"}
        
        workflow = self.active_workflows[workflow_id]
        workflow["status"] = "running"
        workflow["started_at"] = datetime.now().isoformat()
        
        # Execute tasks respecting dependencies
        execution_results = []
        completed_tasks = set()
        
        while True:
            # Find tasks ready to execute
            ready_tasks = []
            for task_assignment in workflow["tasks"]:
                if task_assignment["status"] == "pending":
                    # Check if dependencies are satisfied
                    deps = set(task_assignment["dependencies"])
                    if deps.issubset(completed_tasks):
                        ready_tasks.append(task_assignment)
            
            if not ready_tasks:
                break
            
            # Execute ready tasks in parallel
            for task_assignment in ready_tasks:
                if task_assignment["assigned_to"]:
                    # Send task to agent
                    result = self._execute_task_on_agent(
                        task_assignment["assigned_to"],
                        task_assignment["task"]
                    )
                    
                    task_assignment["status"] = "completed" if result["success"] else "failed"
                    task_assignment["result"] = result
                    task_assignment["completed_at"] = datetime.now().isoformat()
                    
                    if result["success"]:
                        task_id = task_assignment["task"].get("id", "unnamed")
                        completed_tasks.add(task_id)
                    
                    execution_results.append(result)
                else:
                    task_assignment["status"] = "skipped"
                    task_assignment["reason"] = "No agent assigned"
            
            # Update workflow progress
            total_tasks = len(workflow["tasks"])
            completed = len([t for t in workflow["tasks"] if t["status"] in ["completed", "failed", "skipped"]])
            workflow["progress"] = int((completed / total_tasks) * 100)
        
        # Final workflow status
        failed_tasks = [t for t in workflow["tasks"] if t["status"] == "failed"]
        if failed_tasks:
            workflow["status"] = "failed"
        else:
            workflow["status"] = "completed"
        
        workflow["completed_at"] = datetime.now().isoformat()
        
        # Update knowledge base
        self.store_knowledge(f"workflow_{workflow_id}_result", workflow, category="workflow_results")
        
        return {
            "success": workflow["status"] == "completed",
            "workflow_id": workflow_id,
            "progress": workflow["progress"],
            "results": execution_results,
            "failed_tasks": len(failed_tasks)
        }
    
    def _execute_task_on_agent(self, agent_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task on a specific agent"""
        start_time = datetime.now()
        
        # Add task to agent's queue
        self.agent_registry[agent_id]["current_tasks"].append(task)
        
        # Send task to agent via task queue
        task_id = self.add_task_to_queue({
            "assigned_to": agent_id,
            "task": task,
            "coordinator": self.agent_id
        })
        
        # Notify agent
        self.communicate(agent_id, {
            "type": "task_assignment",
            "task_id": task_id,
            "task": task,
            "from": self.agent_id
        })
        
        # In a real system, we would wait for the agent to complete the task
        # For now, simulate task completion
        result = {
            "success": True,
            "task_id": task_id,
            "agent_id": agent_id,
            "task_type": task.get("type", "unknown"),
            "execution_time": (datetime.now() - start_time).total_seconds(),
            "result": f"Task {task.get('type', 'unknown')} completed by {agent_id}"
        }
        
        # Update agent performance metrics
        self._update_agent_performance(agent_id, result)
        
        # Remove task from agent's current tasks
        self.agent_registry[agent_id]["current_tasks"].remove(task)
        
        return result
    
    def _update_agent_performance(self, agent_id: str, task_result: Dict[str, Any]):
        """Update agent performance metrics based on task results"""
        performance = self.agent_registry[agent_id]["performance"]
        
        if task_result["success"]:
            performance["tasks_completed"] += 1
        else:
            performance["tasks_failed"] += 1
        
        # Update average completion time
        total_tasks = performance["tasks_completed"] + performance["tasks_failed"]
        if total_tasks > 0:
            current_avg = performance["average_completion_time"]
            new_time = task_result.get("execution_time", 0)
            performance["average_completion_time"] = (
                (current_avg * (total_tasks - 1) + new_time) / total_tasks
            )
        
        # Update reliability score
        if total_tasks > 0:
            performance["reliability_score"] = performance["tasks_completed"] / total_tasks
        
        # Store updated metrics
        self.performance_metrics[agent_id][datetime.now().isoformat()] = performance.copy()
    
    def monitor_agent_health(self) -> Dict[str, Any]:
        """Monitor health and status of all agents"""
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(self.agent_registry),
            "healthy_agents": 0,
            "busy_agents": 0,
            "idle_agents": 0,
            "agent_status": {}
        }
        
        for agent_id, agent_info in self.agent_registry.items():
            # Check agent responsiveness
            messages = self._check_agent_messages(agent_id)
            
            # Determine health status
            current_tasks = len(agent_info["current_tasks"])
            reliability = agent_info["performance"]["reliability_score"]
            
            if reliability < 0.5:
                status = "unhealthy"
            elif current_tasks > 5:
                status = "overloaded"
                health_report["busy_agents"] += 1
            elif current_tasks > 0:
                status = "busy"
                health_report["busy_agents"] += 1
            else:
                status = "idle"
                health_report["idle_agents"] += 1
            
            if status not in ["unhealthy", "overloaded"]:
                health_report["healthy_agents"] += 1
            
            health_report["agent_status"][agent_id] = {
                "status": status,
                "current_tasks": current_tasks,
                "reliability_score": reliability,
                "unread_messages": len([m for m in messages if not m.get("read", True)])
            }
        
        # Store health report
        self.store_knowledge(
            f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            health_report,
            category="health_monitoring"
        )
        
        return health_report
    
    def _check_agent_messages(self, agent_id: str) -> List[Dict[str, Any]]:
        """Check messages for a specific agent"""
        msg_file = self.shared_memory / "agent-messages" / f"{agent_id}.json"
        
        if msg_file.exists():
            try:
                with open(msg_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def optimize_task_distribution(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Optimize distribution of tasks across agents"""
        # Group tasks by type
        task_groups = defaultdict(list)
        for task in tasks:
            task_type = task.get("type", "general")
            task_groups[task_type].append(task)
        
        # Assign tasks to agents optimally
        distribution = defaultdict(list)
        
        for task_type, type_tasks in task_groups.items():
            # Find agents capable of handling this task type
            capable_agents = []
            for agent_id, agent_info in self.agent_registry.items():
                if self._agent_can_handle_task_type(agent_id, task_type):
                    capable_agents.append((agent_id, agent_info))
            
            if not capable_agents:
                # No capable agents - add to unassigned
                distribution["unassigned"].extend(type_tasks)
                continue
            
            # Distribute tasks among capable agents based on current load
            agent_loads = {
                agent_id: len(info["current_tasks"]) 
                for agent_id, info in capable_agents
            }
            
            for task in type_tasks:
                # Assign to least loaded agent
                min_load_agent = min(agent_loads, key=agent_loads.get)
                distribution[min_load_agent].append(task)
                agent_loads[min_load_agent] += 1
        
        return dict(distribution)
    
    def _agent_can_handle_task_type(self, agent_id: str, task_type: str) -> bool:
        """Check if an agent can handle a specific task type"""
        # Simple matching based on agent specialization
        specializations = {
            "infrastructure": ["deploy", "scale", "monitor", "infrastructure"],
            "tool-creator": ["create_tool", "generate_tool", "api_tool"],
            "api-explorer": ["discover_api", "test_api", "api_wrapper"],
            "database-admin": ["database", "query", "backup", "migration"]
        }
        
        for spec_key, task_types in specializations.items():
            if spec_key in agent_id:
                return any(t in task_type.lower() for t in task_types)
        
        return False
    
    def create_agent_pipeline(self, pipeline_name: str, stages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a pipeline where output from one agent feeds into the next"""
        pipeline_id = f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{pipeline_name}"
        
        # Validate and prepare stages
        prepared_stages = []
        for i, stage in enumerate(stages):
            agent_id = self._find_best_agent_for_task(stage)
            prepared_stage = {
                "stage_number": i + 1,
                "agent_id": agent_id,
                "task": stage,
                "input_from": i if i > 0 else None,
                "output_to": i + 2 if i < len(stages) - 1 else None,
                "status": "pending"
            }
            prepared_stages.append(prepared_stage)
        
        pipeline = {
            "id": pipeline_id,
            "name": pipeline_name,
            "created_at": datetime.now().isoformat(),
            "stages": prepared_stages,
            "status": "created",
            "current_stage": 0
        }
        
        # Store pipeline
        self.store_knowledge(f"pipeline_{pipeline_id}", pipeline, category="pipelines")
        
        return pipeline
    
    def resolve_agent_conflict(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflicts between agents competing for resources"""
        conflict_type = conflict.get("type", "resource")
        agents_involved = conflict.get("agents", [])
        resource = conflict.get("resource", "")
        
        resolution = {
            "conflict_id": f"conflict_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "type": conflict_type,
            "agents": agents_involved,
            "resource": resource,
            "resolution": None,
            "timestamp": datetime.now().isoformat()
        }
        
        if conflict_type == "resource":
            # Resolve based on priority and current workload
            agent_priorities = []
            for agent_id in agents_involved:
                if agent_id in self.agent_registry:
                    agent_info = self.agent_registry[agent_id]
                    priority_score = (
                        agent_info["performance"]["reliability_score"] * 10 -
                        len(agent_info["current_tasks"])
                    )
                    agent_priorities.append((agent_id, priority_score))
            
            # Assign resource to highest priority agent
            if agent_priorities:
                agent_priorities.sort(key=lambda x: x[1], reverse=True)
                winner = agent_priorities[0][0]
                resolution["resolution"] = f"Resource assigned to {winner}"
                resolution["winner"] = winner
                
                # Notify agents
                for agent_id in agents_involved:
                    self.communicate(agent_id, {
                        "type": "conflict_resolution",
                        "conflict_id": resolution["conflict_id"],
                        "resource": resource,
                        "granted": agent_id == winner
                    })
        
        elif conflict_type == "task":
            # Multiple agents trying to handle same task
            resolution["resolution"] = "Task reassigned to most suitable agent"
            best_agent = self._find_best_agent_for_task(conflict.get("task", {}))
            resolution["winner"] = best_agent
        
        # Store conflict resolution
        self.store_knowledge(
            f"conflict_{resolution['conflict_id']}",
            resolution,
            category="conflict_resolutions"
        )
        
        return resolution
    
    def scale_agent_capacity(self, agent_type: str, scale_factor: int = 2) -> Dict[str, Any]:
        """Scale agent capacity by spawning additional instances"""
        # Find agent template
        template_agent = None
        for agent_id in self.agent_registry:
            if agent_type in agent_id:
                template_agent = agent_id
                break
        
        if not template_agent:
            return {"success": False, "error": f"No agent of type {agent_type} found"}
        
        # Spawn new agents
        spawned_agents = []
        for i in range(scale_factor - 1):  # -1 because we already have one
            new_agent_config = {
                "type": agent_type,
                "capabilities": self.agent_registry[template_agent]["capabilities"],
                "instance_number": i + 2  # Start from 2 since 1 exists
            }
            
            result = self.spawn_agent(agent_type, new_agent_config)
            spawned_agents.append(result)
        
        return {
            "success": True,
            "agent_type": agent_type,
            "original_capacity": 1,
            "new_capacity": scale_factor,
            "spawned_agents": spawned_agents
        }
    
    def handle_agent_failure(self, failed_agent_id: str, failure_reason: str) -> Dict[str, Any]:
        """Handle agent failures and reassign tasks"""
        if failed_agent_id not in self.agent_registry:
            return {"success": False, "error": f"Agent {failed_agent_id} not found"}
        
        agent_info = self.agent_registry[failed_agent_id]
        
        # Mark agent as failed
        agent_info["status"] = "failed"
        agent_info["failure_reason"] = failure_reason
        agent_info["failed_at"] = datetime.now().isoformat()
        
        # Get agent's current tasks
        orphaned_tasks = agent_info["current_tasks"].copy()
        agent_info["current_tasks"] = []
        
        # Reassign tasks to other agents
        reassignments = []
        for task in orphaned_tasks:
            new_agent = self._find_best_agent_for_task(task)
            if new_agent and new_agent != failed_agent_id:
                reassignments.append({
                    "task": task,
                    "from_agent": failed_agent_id,
                    "to_agent": new_agent
                })
                
                # Execute on new agent
                self._execute_task_on_agent(new_agent, task)
            else:
                reassignments.append({
                    "task": task,
                    "from_agent": failed_agent_id,
                    "to_agent": None,
                    "reason": "No suitable replacement found"
                })
        
        # Create recovery report
        recovery_report = {
            "failed_agent": failed_agent_id,
            "failure_reason": failure_reason,
            "timestamp": datetime.now().isoformat(),
            "orphaned_tasks": len(orphaned_tasks),
            "reassignments": reassignments,
            "recovery_status": "completed" if all(r["to_agent"] for r in reassignments) else "partial"
        }
        
        # Store recovery report
        self.store_knowledge(
            f"recovery_{failed_agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            recovery_report,
            category="failure_recovery"
        )
        
        return recovery_report
    
    def generate_coordination_report(self) -> Dict[str, Any]:
        """Generate comprehensive coordination report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "coordinator": self.agent_id,
            "system_overview": {
                "total_agents": len(self.agent_registry),
                "active_agents": len([a for a in self.agent_registry.values() if a["status"] == "available"]),
                "failed_agents": len([a for a in self.agent_registry.values() if a["status"] == "failed"]),
                "total_workflows": len(self.active_workflows),
                "completed_workflows": len([w for w in self.active_workflows.values() if w["status"] == "completed"])
            },
            "agent_performance": {},
            "workflow_statistics": {},
            "resource_utilization": {},
            "recommendations": []
        }
        
        # Agent performance summary
        for agent_id, agent_info in self.agent_registry.items():
            perf = agent_info["performance"]
            report["agent_performance"][agent_id] = {
                "reliability": perf["reliability_score"],
                "tasks_completed": perf["tasks_completed"],
                "tasks_failed": perf["tasks_failed"],
                "avg_completion_time": perf["average_completion_time"],
                "current_load": len(agent_info["current_tasks"])
            }
        
        # Workflow statistics
        total_tasks = 0
        completed_tasks = 0
        failed_tasks = 0
        
        for workflow in self.active_workflows.values():
            for task in workflow["tasks"]:
                total_tasks += 1
                if task["status"] == "completed":
                    completed_tasks += 1
                elif task["status"] == "failed":
                    failed_tasks += 1
        
        report["workflow_statistics"] = {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": completed_tasks / total_tasks if total_tasks > 0 else 0
        }
        
        # Resource utilization
        agent_utilization = {}
        for agent_id, agent_info in self.agent_registry.items():
            current_tasks = len(agent_info["current_tasks"])
            if current_tasks == 0:
                utilization = "idle"
            elif current_tasks <= 2:
                utilization = "low"
            elif current_tasks <= 5:
                utilization = "medium"
            else:
                utilization = "high"
            
            agent_utilization[agent_id] = utilization
        
        report["resource_utilization"] = agent_utilization
        
        # Generate recommendations
        idle_agents = [a for a, u in agent_utilization.items() if u == "idle"]
        overloaded_agents = [a for a, u in agent_utilization.items() if u == "high"]
        
        if idle_agents:
            report["recommendations"].append(
                f"Consider assigning more tasks to idle agents: {', '.join(idle_agents)}"
            )
        
        if overloaded_agents:
            report["recommendations"].append(
                f"Consider scaling or redistributing tasks from overloaded agents: {', '.join(overloaded_agents)}"
            )
        
        low_reliability_agents = [
            a for a, info in self.agent_registry.items() 
            if info["performance"]["reliability_score"] < 0.7
        ]
        
        if low_reliability_agents:
            report["recommendations"].append(
                f"Investigate low reliability agents: {', '.join(low_reliability_agents)}"
            )
        
        # Store report
        self.store_knowledge(
            f"coordination_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            report,
            category="coordination_reports"
        )
        
        return report
    
    def process_message(self, message: str) -> str:
        """Process incoming messages about coordination"""
        message_lower = message.lower()
        
        # Check if asking about agent status
        if "status" in message_lower or "health" in message_lower:
            health_report = self.monitor_agent_health()
            return f"System status: {health_report['healthy_agents']}/{health_report['total_agents']} agents healthy. {health_report['busy_agents']} busy, {health_report['idle_agents']} idle."
        
        # Check if asking to create workflow
        if "workflow" in message_lower and "create" in message_lower:
            # Demo workflow
            tasks = [
                {"id": "task1", "type": "discover_api", "url": "https://api.example.com"},
                {"id": "task2", "type": "create_tool", "dependencies": ["task1"]},
                {"id": "task3", "type": "test_api", "dependencies": ["task2"]}
            ]
            workflow = self.create_workflow("api_integration", tasks)
            return f"Created workflow {workflow['id']} with {len(workflow['tasks'])} tasks"
        
        # Check if asking to execute workflow
        if "execute" in message_lower and "workflow" in message_lower:
            if self.active_workflows:
                workflow_id = list(self.active_workflows.keys())[0]
                result = self.execute_workflow(workflow_id)
                return f"Workflow execution: Success={result['success']}, Progress={result['progress']}%, Failed tasks={result['failed_tasks']}"
            else:
                return "No workflows available to execute. Create a workflow first."
        
        # Check if asking about task distribution
        if "distribute" in message_lower or "optimize" in message_lower:
            # Demo tasks
            demo_tasks = [
                {"type": "infrastructure", "name": "Deploy service"},
                {"type": "database", "name": "Create backup"},
                {"type": "api_tool", "name": "Generate wrapper"},
                {"type": "infrastructure", "name": "Scale service"}
            ]
            distribution = self.optimize_task_distribution(demo_tasks)
            assigned_count = sum(len(tasks) for agent, tasks in distribution.items() if agent != "unassigned")
            return f"Optimized distribution: {assigned_count} tasks assigned across {len(distribution)-1 if 'unassigned' in distribution else len(distribution)} agents"
        
        # Check if asking for report
        if "report" in message_lower:
            report = self.generate_coordination_report()
            overview = report["system_overview"]
            return f"Coordination Report: {overview['active_agents']} active agents, {overview['completed_workflows']} workflows completed. Success rate: {report['workflow_statistics']['success_rate']:.1%}"
        
        # Check if asking about conflicts
        if "conflict" in message_lower:
            # Demo conflict resolution
            conflict = {
                "type": "resource",
                "agents": ["agent-01-infrastructure", "agent-02-tool-creator"],
                "resource": "database_connection"
            }
            resolution = self.resolve_agent_conflict(conflict)
            return f"Resolved conflict {resolution['conflict_id']}: {resolution['resolution']}"
        
        return f"Coordinator ready. I can create workflows, distribute tasks, monitor agents, and optimize system performance. Current agents: {len(self.agent_registry)}"
    
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute coordination tasks"""
        task_type = task.get("type", "")
        
        if task_type == "create_workflow":
            workflow_name = task.get("name", "unnamed")
            tasks = task.get("tasks", [])
            result = self.create_workflow(workflow_name, tasks)
            return {"status": "completed", "result": result}
        
        elif task_type == "execute_workflow":
            workflow_id = task.get("workflow_id", "")
            result = self.execute_workflow(workflow_id)
            return {"status": "completed", "result": result}
        
        elif task_type == "monitor_health":
            result = self.monitor_agent_health()
            return {"status": "completed", "result": result}
        
        elif task_type == "optimize_distribution":
            tasks = task.get("tasks", [])
            result = self.optimize_task_distribution(tasks)
            return {"status": "completed", "result": result}
        
        elif task_type == "resolve_conflict":
            conflict = task.get("conflict", {})
            result = self.resolve_agent_conflict(conflict)
            return {"status": "completed", "result": result}
        
        elif task_type == "scale_agent":
            agent_type = task.get("agent_type", "")
            scale_factor = task.get("scale_factor", 2)
            result = self.scale_agent_capacity(agent_type, scale_factor)
            return {"status": "completed", "result": result}
        
        elif task_type == "generate_report":
            result = self.generate_coordination_report()
            return {"status": "completed", "result": result}
        
        else:
            return {"status": "error", "result": f"Unknown task type: {task_type}"}


# Agent initialization
if __name__ == "__main__":
    agent = CoordinatorAgent()
    print(f"Coordinator Agent initialized: {agent.agent_id}")
    print(f"Capabilities: {agent.capabilities}")
    print(f"\nDiscovered agents: {list(agent.agent_registry.keys())}")
    
    # Test agent health monitoring
    health = agent.monitor_agent_health()
    print(f"\nAgent health report:")
    print(f"Total agents: {health['total_agents']}")
    print(f"Healthy agents: {health['healthy_agents']}")
    
    # Test workflow creation
    demo_tasks = [
        {"id": "t1", "type": "infrastructure", "name": "Create instance"},
        {"id": "t2", "type": "database", "name": "Setup database", "dependencies": ["t1"]},
        {"id": "t3", "type": "api_tool", "name": "Create API tools", "dependencies": ["t2"]}
    ]
    workflow = agent.create_workflow("demo_workflow", demo_tasks)
    print(f"\nCreated workflow: {workflow['id']} with {len(workflow['tasks'])} tasks")

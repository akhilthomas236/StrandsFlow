"""Orchestrator for multi-agent workflows in StrandsFlow."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from enum import Enum

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from strands import Agent, tool
from strands_tools import use_agent

from ..core.agent import StrandsFlowAgent
from .a2a_server import A2AServerManager, A2AServer


class WorkflowType(Enum):
    """Types of multi-agent workflows."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"  
    CONDITIONAL = "conditional"
    SWARM = "swarm"


class Orchestrator:
    """
    Multi-agent orchestrator for StrandsFlow.
    
    Manages workflows across multiple specialized agents using different patterns:
    - Sequential: Pass tasks through agents in order
    - Parallel: Execute tasks simultaneously across agents
    - Conditional: Route tasks based on content analysis
    - Swarm: Dynamic agent selection and collaboration
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        a2a_manager: Optional[A2AServerManager] = None
    ):
        """Initialize the orchestrator."""
        self.agents: Dict[str, StrandsFlowAgent] = {}
        self.a2a_manager = a2a_manager or A2AServerManager()
        self.orchestrator_agent: Optional[Agent] = None
        
        logger.info("Orchestrator initialized")
    
    def add_specialist(
        self,
        name: str,
        agent: StrandsFlowAgent,
        role: str,
        capabilities: List[str]
    ) -> None:
        """Add a specialist agent to the orchestrator."""
        self.agents[name] = agent
        
        # Register with A2A manager
        self.a2a_manager.add_agent(agent, name)
        
        # Store metadata
        agent._role = role
        agent._capabilities = capabilities
        
        logger.info(
            "Added specialist agent",
            name=name,
            role=role,
            capabilities=capabilities
        )
    
    def create_orchestrator_agent(self, system_prompt: Optional[str] = None) -> Agent:
        """Create the main orchestrator agent with access to all specialists."""
        if not system_prompt:
            system_prompt = self._get_default_orchestrator_prompt()
        
        # Get tools for all specialist agents
        specialist_tools = self.a2a_manager.get_agent_tools()
        
        # Create orchestrator with specialist tools
        from strands.models import BedrockModel
        from strands_tools import calculator, current_time, file_read, python_repl
        
        model = BedrockModel(
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            region_name="us-west-2",
            temperature=0.3
        )
        
        all_tools = [calculator, current_time, file_read, python_repl] + specialist_tools
        
        self.orchestrator_agent = Agent(
            model=model,
            tools=all_tools,
            system_prompt=system_prompt
        )
        
        logger.info(
            "Created orchestrator agent",
            num_specialists=len(self.agents),
            num_tools=len(all_tools)
        )
        
        return self.orchestrator_agent
    
    async def execute_workflow(
        self,
        task: str,
        workflow_type: WorkflowType = WorkflowType.CONDITIONAL,
        agents: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Execute a multi-agent workflow."""
        if not self.orchestrator_agent:
            self.create_orchestrator_agent()
        
        try:
            if workflow_type == WorkflowType.SEQUENTIAL:
                return await self._execute_sequential(task, agents)
            elif workflow_type == WorkflowType.PARALLEL:
                return await self._execute_parallel(task, agents)
            elif workflow_type == WorkflowType.CONDITIONAL:
                return await self._execute_conditional(task)
            elif workflow_type == WorkflowType.SWARM:
                return await self._execute_swarm(task)
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")
                
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "workflow_type": workflow_type.value
            }
    
    async def _execute_sequential(
        self,
        task: str,
        agent_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Execute task sequentially through specified agents."""
        if not agent_names:
            agent_names = list(self.agents.keys())
        
        results = []
        current_input = task
        
        for agent_name in agent_names:
            if agent_name not in self.agents:
                logger.warning(f"Agent {agent_name} not found, skipping")
                continue
            
            agent = self.agents[agent_name]
            
            try:
                response = await agent.chat(current_input)
                result = {
                    "agent": agent_name,
                    "input": current_input,
                    "output": response,
                    "status": "success"
                }
                results.append(result)
                current_input = response  # Chain output to next agent
                
            except Exception as e:
                result = {
                    "agent": agent_name,
                    "input": current_input,
                    "error": str(e),
                    "status": "error"
                }
                results.append(result)
                break  # Stop on error
        
        return {
            "status": "success",
            "workflow_type": "sequential",
            "results": results,
            "final_output": results[-1]["output"] if results and results[-1]["status"] == "success" else None
        }
    
    async def _execute_parallel(
        self,
        task: str,
        agent_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Execute task in parallel across specified agents."""
        if not agent_names:
            agent_names = list(self.agents.keys())
        
        # Create tasks for parallel execution
        tasks = []
        for agent_name in agent_names:
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                task_coroutine = self._run_agent_task(agent, agent_name, task)
                tasks.append(task_coroutine)
        
        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "agent": agent_names[i],
                    "status": "error",
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return {
            "status": "success",
            "workflow_type": "parallel",
            "results": processed_results
        }
    
    async def _execute_conditional(self, task: str) -> Dict[str, Any]:
        """Use orchestrator to intelligently route task to appropriate specialist."""
        routing_prompt = f"""
        Analyze this task and route it to the most appropriate specialist agent:
        
        Task: {task}
        
        Available specialists:
        {self._format_specialist_list()}
        
        Consider the task requirements and route it to the best agent(s).
        You can use multiple agents if needed for complex tasks.
        """
        
        result = self.orchestrator_agent(routing_prompt)
        
        return {
            "status": "success", 
            "workflow_type": "conditional",
            "routing_decision": result.message,
            "task": task
        }
    
    async def _execute_swarm(self, task: str) -> Dict[str, Any]:
        """Execute dynamic swarm-based collaboration."""
        swarm_prompt = f"""
        Coordinate a swarm of specialist agents to complete this complex task:
        
        Task: {task}
        
        Available specialists:
        {self._format_specialist_list()}
        
        Break down the task, assign work to appropriate specialists, 
        and coordinate their efforts to produce a comprehensive result.
        """
        
        result = self.orchestrator_agent(swarm_prompt)
        
        return {
            "status": "success",
            "workflow_type": "swarm", 
            "coordination_result": result.message,
            "task": task
        }
    
    async def _run_agent_task(
        self,
        agent: StrandsFlowAgent,
        agent_name: str,
        task: str
    ) -> Dict[str, Any]:
        """Run a task on a specific agent."""
        try:
            response = await agent.chat(task)
            return {
                "agent": agent_name,
                "input": task,
                "output": response,
                "status": "success"
            }
        except Exception as e:
            return {
                "agent": agent_name,
                "input": task,
                "error": str(e),
                "status": "error"
            }
    
    def _format_specialist_list(self) -> str:
        """Format list of available specialists for prompts."""
        specialist_info = []
        for name, agent in self.agents.items():
            role = getattr(agent, '_role', 'General Assistant')
            capabilities = getattr(agent, '_capabilities', [])
            specialist_info.append(f"- {name}: {role} (Capabilities: {', '.join(capabilities)})")
        
        return "\n".join(specialist_info)
    
    def _get_default_orchestrator_prompt(self) -> str:
        """Get default system prompt for orchestrator."""
        return f"""You are an intelligent orchestrator managing a team of specialist AI agents.

Your role is to:
1. Analyze incoming tasks and understand their requirements
2. Route tasks to the most appropriate specialist agent(s)
3. Coordinate multi-agent workflows when needed
4. Synthesize results from multiple agents
5. Ensure high-quality, comprehensive responses

Available specialist agents:
{self._format_specialist_list()}

For each task:
- Assess the complexity and requirements
- Choose the best agent(s) for the job
- Use sequential processing for dependent tasks
- Use parallel processing for independent subtasks
- Coordinate collaboration for complex multi-faceted tasks

Always explain your routing decisions and provide clear, actionable results."""
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestrator metrics."""
        return {
            "num_specialists": len(self.agents),
            "specialist_names": list(self.agents.keys()),
            "has_orchestrator": self.orchestrator_agent is not None,
            "a2a_agents": len(self.a2a_manager.servers)
        }

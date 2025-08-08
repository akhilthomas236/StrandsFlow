"""Workflow manager for complex multi-agent tasks in StrandsFlow."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from .orchestrator import Orchestrator, WorkflowType
from .specialist_pool import SpecialistPool
from ..core.agent import StrandsFlowAgent


@dataclass
class WorkflowStep:
    """Definition of a workflow step."""
    name: str
    agent: str
    input_template: str
    depends_on: Optional[List[str]] = None
    condition: Optional[str] = None
    retry_count: int = 3


@dataclass
class WorkflowDefinition:
    """Definition of a complete workflow."""
    name: str
    description: str
    steps: List[WorkflowStep]
    output_format: Optional[str] = None


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowExecution:
    """Workflow execution state."""
    workflow_id: str
    workflow_name: str
    status: WorkflowStatus
    current_step: Optional[str] = None
    results: Dict[str, Any] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class WorkflowManager:
    """
    Manager for complex multi-agent workflows.
    
    Provides capabilities for:
    - Defining multi-step workflows
    - Managing workflow execution state
    - Handling dependencies between steps
    - Error handling and retries
    - Progress tracking and monitoring
    """
    
    def __init__(
        self,
        orchestrator: Orchestrator,
        specialist_pool: SpecialistPool
    ):
        """Initialize workflow manager."""
        self.orchestrator = orchestrator
        self.specialist_pool = specialist_pool
        
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        
        # Predefined workflows
        self._register_predefined_workflows()
        
        logger.info("Workflow manager initialized")
    
    def register_workflow(self, workflow: WorkflowDefinition) -> None:
        """Register a workflow definition."""
        self.workflows[workflow.name] = workflow
        logger.info(f"Registered workflow: {workflow.name}")
    
    async def execute_workflow(
        self,
        workflow_name: str,
        inputs: Dict[str, Any],
        execution_id: Optional[str] = None
    ) -> str:
        """Execute a workflow and return execution ID."""
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        workflow = self.workflows[workflow_name]
        exec_id = execution_id or f"{workflow_name}_{len(self.executions)}"
        
        # Create execution state
        execution = WorkflowExecution(
            workflow_id=exec_id,
            workflow_name=workflow_name,
            status=WorkflowStatus.PENDING,
            results={}
        )
        
        self.executions[exec_id] = execution
        
        # Start execution in background
        asyncio.create_task(self._run_workflow(exec_id, workflow, inputs))
        
        return exec_id
    
    async def _run_workflow(
        self,
        execution_id: str,
        workflow: WorkflowDefinition,
        inputs: Dict[str, Any]
    ) -> None:
        """Run a workflow execution."""
        import time
        
        execution = self.executions[execution_id]
        execution.status = WorkflowStatus.RUNNING
        execution.start_time = time.time()
        execution.results = {"inputs": inputs, "steps": {}}
        
        try:
            # Build dependency graph
            step_map = {step.name: step for step in workflow.steps}
            completed_steps = set()
            step_results = {}
            
            while len(completed_steps) < len(workflow.steps):
                # Find ready steps (dependencies satisfied)
                ready_steps = []
                for step in workflow.steps:
                    if step.name in completed_steps:
                        continue
                    
                    if not step.depends_on or all(dep in completed_steps for dep in step.depends_on):
                        ready_steps.append(step)
                
                if not ready_steps:
                    raise RuntimeError("Circular dependency or unsatisfiable dependencies detected")
                
                # Execute ready steps (can be parallel)
                step_tasks = []
                for step in ready_steps:
                    task = self._execute_step(step, step_results, inputs)
                    step_tasks.append((step.name, task))
                
                # Wait for step completion
                for step_name, task in step_tasks:
                    try:
                        result = await task
                        step_results[step_name] = result
                        completed_steps.add(step_name)
                        execution.results["steps"][step_name] = result
                        execution.current_step = step_name
                        
                        logger.info(f"Completed step {step_name} in workflow {execution_id}")
                        
                    except Exception as e:
                        logger.error(f"Step {step_name} failed in workflow {execution_id}: {e}")
                        execution.status = WorkflowStatus.FAILED
                        execution.error = f"Step {step_name} failed: {str(e)}"
                        execution.end_time = time.time()
                        return
            
            # Workflow completed successfully
            execution.status = WorkflowStatus.COMPLETED
            execution.end_time = time.time()
            
            # Apply output formatting if specified
            if workflow.output_format:
                execution.results["formatted_output"] = await self._format_output(
                    workflow.output_format,
                    step_results
                )
            
            logger.info(f"Workflow {execution_id} completed successfully")
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            execution.end_time = time.time()
            logger.error(f"Workflow {execution_id} failed: {e}")
    
    async def _execute_step(
        self,
        step: WorkflowStep,
        step_results: Dict[str, Any],
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single workflow step."""
        # Prepare input for this step
        step_input = self._prepare_step_input(step.input_template, step_results, inputs)
        
        # Check condition if specified
        if step.condition and not self._evaluate_condition(step.condition, step_results, inputs):
            return {"status": "skipped", "reason": "condition not met"}
        
        # Get the agent
        agent = self.specialist_pool.get_specialist(step.agent)
        if not agent:
            # Try orchestrator for direct execution
            if step.agent == "orchestrator":
                result = await self.orchestrator.execute_workflow(
                    step_input,
                    WorkflowType.CONDITIONAL
                )
                return result
            else:
                raise ValueError(f"Agent '{step.agent}' not found")
        
        # Execute with retries
        for attempt in range(step.retry_count):
            try:
                result = await agent.chat(step_input)
                return {
                    "status": "success",
                    "output": result,
                    "agent": step.agent,
                    "attempt": attempt + 1
                }
            except Exception as e:
                if attempt == step.retry_count - 1:
                    raise
                logger.warning(f"Step {step.name} attempt {attempt + 1} failed: {e}")
    
    def _prepare_step_input(
        self,
        template: str,
        step_results: Dict[str, Any],
        inputs: Dict[str, Any]
    ) -> str:
        """Prepare input for a step using template and previous results."""
        # Simple template replacement
        context = {"inputs": inputs, "steps": step_results}
        
        # Replace {inputs.key} and {steps.step_name.output} patterns
        import re
        
        def replace_var(match):
            var_path = match.group(1)
            parts = var_path.split('.')
            
            try:
                value = context
                for part in parts:
                    value = value[part]
                return str(value)
            except (KeyError, TypeError):
                return match.group(0)  # Return original if not found
        
        result = re.sub(r'\\{([^}]+)\\}', replace_var, template)
        return result
    
    def _evaluate_condition(
        self,
        condition: str,
        step_results: Dict[str, Any],
        inputs: Dict[str, Any]
    ) -> bool:
        """Evaluate a simple condition."""
        # Simple condition evaluation - can be extended
        context = {"inputs": inputs, "steps": step_results}
        
        try:
            # Very basic condition evaluation
            # In production, use a proper expression evaluator
            if "success" in condition:
                # Check if previous steps were successful
                for step_name, result in step_results.items():
                    if isinstance(result, dict) and result.get("status") != "success":
                        return False
                return True
            
            return True  # Default to true for unknown conditions
            
        except Exception:
            return False
    
    async def _format_output(
        self,
        template: str,
        step_results: Dict[str, Any]
    ) -> str:
        """Format final workflow output."""
        # Use orchestrator to format the final output
        format_prompt = f"""
        Format the following workflow results according to this template:
        
        Template: {template}
        
        Results: {step_results}
        
        Create a well-structured, comprehensive summary.
        """
        
        if self.orchestrator.orchestrator_agent:
            result = self.orchestrator.orchestrator_agent(format_prompt)
            return result.message
        else:
            return str(step_results)
    
    def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get workflow execution status."""
        return self.executions.get(execution_id)
    
    def list_workflows(self) -> Dict[str, Dict[str, Any]]:
        """List all available workflows."""
        return {
            name: {
                "name": workflow.name,
                "description": workflow.description,
                "steps": [step.name for step in workflow.steps],
                "step_count": len(workflow.steps)
            }
            for name, workflow in self.workflows.items()
        }
    
    def list_executions(self) -> Dict[str, Dict[str, Any]]:
        """List all workflow executions."""
        return {
            exec_id: {
                "workflow_name": execution.workflow_name,
                "status": execution.status.value,
                "current_step": execution.current_step,
                "start_time": execution.start_time,
                "end_time": execution.end_time,
                "error": execution.error
            }
            for exec_id, execution in self.executions.items()
        }
    
    def _register_predefined_workflows(self) -> None:
        """Register predefined workflows."""
        
        # Content Creation Workflow
        content_workflow = WorkflowDefinition(
            name="content_creation",
            description="End-to-end content creation with research, writing, and review",
            steps=[
                WorkflowStep(
                    name="research",
                    agent="research_assistant",
                    input_template="Research the topic: {inputs.topic}. Provide comprehensive background information, key points, and current trends."
                ),
                WorkflowStep(
                    name="outline",
                    agent="content_writer",
                    input_template="Based on this research: {steps.research.output}, create a detailed outline for content about {inputs.topic}.",
                    depends_on=["research"]
                ),
                WorkflowStep(
                    name="write_content",
                    agent="content_writer", 
                    input_template="Write engaging content following this outline: {steps.outline.output}. Target audience: {inputs.audience}",
                    depends_on=["outline"]
                ),
                WorkflowStep(
                    name="review",
                    agent="orchestrator",
                    input_template="Review this content for quality, accuracy, and engagement: {steps.write_content.output}. Suggest improvements.",
                    depends_on=["write_content"]
                )
            ],
            output_format="Create a final content package including the original research, content, and review feedback."
        )
        
        # Software Development Workflow
        dev_workflow = WorkflowDefinition(
            name="software_development",
            description="Complete software development cycle from requirements to deployment",
            steps=[
                WorkflowStep(
                    name="analyze_requirements",
                    agent="code_expert",
                    input_template="Analyze these software requirements and create a technical specification: {inputs.requirements}"
                ),
                WorkflowStep(
                    name="design_architecture",
                    agent="code_expert",
                    input_template="Design system architecture based on: {steps.analyze_requirements.output}",
                    depends_on=["analyze_requirements"]
                ),
                WorkflowStep(
                    name="implement_code",
                    agent="code_expert",
                    input_template="Implement code following this architecture: {steps.design_architecture.output}. Language: {inputs.language}",
                    depends_on=["design_architecture"]
                ),
                WorkflowStep(
                    name="code_review",
                    agent="code_expert",
                    input_template="Perform code review on: {steps.implement_code.output}. Check for bugs, security issues, and best practices.",
                    depends_on=["implement_code"]
                ),
                WorkflowStep(
                    name="documentation",
                    agent="content_writer",
                    input_template="Create technical documentation for this code: {steps.implement_code.output}",
                    depends_on=["implement_code"]
                )
            ],
            output_format="Package the complete software solution with code, documentation, and review findings."
        )
        
        # Data Analysis Workflow
        analysis_workflow = WorkflowDefinition(
            name="data_analysis",
            description="Complete data analysis from exploration to insights",
            steps=[
                WorkflowStep(
                    name="data_exploration",
                    agent="data_analyst",
                    input_template="Explore and analyze this dataset: {inputs.dataset}. Provide summary statistics and initial insights."
                ),
                WorkflowStep(
                    name="statistical_analysis",
                    agent="data_analyst",
                    input_template="Perform statistical analysis on: {steps.data_exploration.output}. Research question: {inputs.research_question}",
                    depends_on=["data_exploration"]
                ),
                WorkflowStep(
                    name="visualization",
                    agent="data_analyst",
                    input_template="Create data visualizations for: {steps.statistical_analysis.output}",
                    depends_on=["statistical_analysis"]
                ),
                WorkflowStep(
                    name="insights_report",
                    agent="research_assistant",
                    input_template="Synthesize insights from this analysis: {steps.statistical_analysis.output} and visualizations: {steps.visualization.output}",
                    depends_on=["statistical_analysis", "visualization"]
                )
            ],
            output_format="Create executive summary with key findings, visualizations, and actionable recommendations."
        )
        
        # Register workflows
        for workflow in [content_workflow, dev_workflow, analysis_workflow]:
            self.register_workflow(workflow)

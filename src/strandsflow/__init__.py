"""
StrandsFlow: AI Agent Platform with AWS Bedrock and MCP Integration

A production-ready AI agent platform built on the Strands Agents SDK,
featuring AWS Bedrock model integration, extensible tooling via 
the Model Context Protocol (MCP), and multi-agent orchestration.
"""

from .core.config import StrandsFlowConfig, BedrockConfig, MCPConfig, AgentConfig, APIConfig
from .core.agent import StrandsFlowAgent

# Multi-agent imports (optional, graceful degradation if dependencies missing)
try:
    from .multiagent import (
        A2AServer, A2AServerManager, A2AClient,
        Orchestrator, WorkflowType,
        SpecialistPool, SpecialistConfig, create_predefined_pool,
        WorkflowManager, WorkflowDefinition, WorkflowStep, WorkflowStatus
    )
    MULTIAGENT_AVAILABLE = True
except ImportError:
    MULTIAGENT_AVAILABLE = False

__version__ = "0.1.0"

# Core exports
__all__ = [
    "StrandsFlowConfig",
    "BedrockConfig", 
    "MCPConfig",
    "AgentConfig",
    "APIConfig",
    "StrandsFlowAgent",
]

# Multi-agent exports (if available)
if MULTIAGENT_AVAILABLE:
    __all__.extend([
        "A2AServer",
        "A2AServerManager", 
        "A2AClient",
        "Orchestrator", 
        "WorkflowType",
        "SpecialistPool",
        "SpecialistConfig",
        "create_predefined_pool",
        "WorkflowManager",
        "WorkflowDefinition",
        "WorkflowStep",
        "WorkflowStatus"
    ])
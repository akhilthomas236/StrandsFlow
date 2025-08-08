"""
StrandsFlow: AI Agent Platform with AWS Bedrock and MCP Integration

A production-ready AI agent platform built on the Strands Agents SDK,
featuring AWS Bedrock model integration and extensible tooling via 
the Model Context Protocol (MCP).
"""

from .core.config import StrandsFlowConfig, BedrockConfig, MCPConfig, AgentConfig, APIConfig
from .core.agent import StrandsFlowAgent

__version__ = "0.1.0"
__all__ = [
    "StrandsFlowConfig",
    "BedrockConfig", 
    "MCPConfig",
    "AgentConfig",
    "APIConfig",
    "StrandsFlowAgent",
]
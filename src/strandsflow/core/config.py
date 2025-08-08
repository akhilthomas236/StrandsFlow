"""
StrandsFlow Configuration Management

This module provides configuration management for the StrandsFlow platform,
including AWS Bedrock settings, MCP server configurations, and agent parameters.
"""

import os
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from pathlib import Path


# Default values based on Strands SDK documentation
DEFAULT_BEDROCK_MODEL_ID = "anthropic.claude-sonnet-4-20250514-v1:0"
DEFAULT_BEDROCK_REGION = "us-west-2"  # Default from Strands docs
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 4096


class BedrockConfig(BaseModel):
    """Configuration for AWS Bedrock integration following Strands SDK patterns."""
    
    model_id: str = Field(
        default=DEFAULT_BEDROCK_MODEL_ID,
        description="Bedrock model ID to use"
    )
    region_name: str = Field(
        default=DEFAULT_BEDROCK_REGION,
        description="AWS region for Bedrock (region_name follows boto3 convention)"
    )
    temperature: float = Field(
        default=DEFAULT_TEMPERATURE,
        ge=0.0,
        le=1.0,
        description="Model temperature for response creativity"
    )
    max_tokens: int = Field(
        default=DEFAULT_MAX_TOKENS,
        gt=0,
        description="Maximum tokens in model response"
    )
    streaming: bool = Field(
        default=True,
        description="Enable streaming mode for responses"
    )
    top_p: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Controls diversity via nucleus sampling"
    )
    stop_sequences: Optional[List[str]] = Field(
        default=None,
        description="List of sequences that stop generation"
    )
    cache_prompt: Optional[str] = Field(
        default=None,
        description="Cache point type for the system prompt (e.g., 'default')"
    )
    cache_tools: Optional[str] = Field(
        default=None,
        description="Cache point type for tools (e.g., 'default')"
    )
    # Guardrail settings
    guardrail_id: Optional[str] = Field(
        default=None,
        description="ID of the guardrail to apply"
    )
    guardrail_version: Optional[str] = Field(
        default=None,
        description="Version of the guardrail to apply"
    )
    guardrail_trace: str = Field(
        default="enabled",
        description="Guardrail trace mode ('enabled', 'disabled', 'enabled_full')"
    )


class MCPConfig(BaseModel):
    """Configuration for Model Context Protocol servers following Strands SDK patterns."""
    
    servers: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="MCP server configurations with transport details"
    )
    auto_discover: bool = Field(
        default=True,
        description="Whether to auto-discover MCP servers"
    )
    discovery_paths: List[str] = Field(
        default_factory=lambda: ["~/.mcp/servers", "/usr/local/mcp/servers"],
        description="Paths to search for MCP servers"
    )
    default_transport: str = Field(
        default="stdio",
        description="Default transport type (stdio, sse, streamable_http)"
    )
    connection_timeout: int = Field(
        default=30,
        gt=0,
        description="Connection timeout in seconds"
    )


class AgentConfig(BaseModel):
    """Configuration for StrandsFlow agents."""
    
    name: str = Field(
        default="StrandsFlow Agent",
        description="Agent display name"
    )
    description: str = Field(
        default="AI agent powered by AWS Bedrock and MCP tools",
        description="Agent description"
    )
    max_conversation_turns: int = Field(
        default=50,
        gt=0,
        description="Maximum conversation turns before reset"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        description="Custom system prompt for the agent"
    )
    enable_memory: bool = Field(
        default=True,
        description="Whether to enable conversation memory"
    )


class APIConfig(BaseModel):
    """Configuration for the StrandsFlow API server."""
    
    host: str = Field(
        default="127.0.0.1",
        description="API server host"
    )
    port: int = Field(
        default=8000,
        gt=0,
        le=65535,
        description="API server port"
    )
    workers: int = Field(
        default=1,
        gt=0,
        description="Number of worker processes"
    )
    reload: bool = Field(
        default=False,
        description="Enable auto-reload in development"
    )
    cors_origins: List[str] = Field(
        default_factory=lambda: ["*"],
        description="CORS allowed origins"
    )


class EnvironmentConfig(BaseModel):
    """Environment-specific configuration."""
    
    name: str = Field(
        default="development",
        description="Environment name (development, staging, production)"
    )
    debug: bool = Field(
        default=True,
        description="Enable debug mode"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    enable_metrics: bool = Field(
        default=True,
        description="Enable metrics collection"
    )
    rate_limit_requests: int = Field(
        default=60,
        description="Rate limit requests per minute"
    )
    max_concurrent_connections: int = Field(
        default=100,
        description="Maximum concurrent WebSocket connections"
    )


class A2AConfig(BaseModel):
    """Configuration for Agent-to-Agent (A2A) communication."""
    
    agent_id: str = Field(
        default="default_agent",
        description="Unique identifier for this agent in A2A network"
    )
    server_port: int = Field(
        default=9000,
        description="Port for A2A server to listen on"
    )
    peers: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of peer agents with their endpoints"
    )
    timeout: int = Field(
        default=30,
        description="Timeout for A2A communications in seconds"
    )
    retry_attempts: int = Field(
        default=3,
        description="Number of retry attempts for failed A2A calls"
    )


class StrandsFlowConfig(BaseModel):
    """Main configuration for StrandsFlow platform."""
    
    bedrock: BedrockConfig = Field(
        default_factory=BedrockConfig,
        description="AWS Bedrock configuration"
    )
    mcp: MCPConfig = Field(
        default_factory=MCPConfig,
        description="MCP server configuration"
    )
    agent: AgentConfig = Field(
        default_factory=AgentConfig,
        description="Agent configuration"
    )
    api: APIConfig = Field(
        default_factory=APIConfig,
        description="API server configuration"
    )
    a2a: A2AConfig = Field(
        default_factory=A2AConfig,
        description="Agent-to-Agent communication configuration"
    )
    environment: EnvironmentConfig = Field(
        default_factory=EnvironmentConfig,
        description="Environment-specific configuration"
    )
    
    @classmethod
    def from_env(cls) -> "StrandsFlowConfig":
        """Load configuration from environment variables following AWS/Strands patterns."""
        config = cls()
        
        # Bedrock configuration from environment
        if os.getenv("BEDROCK_MODEL_ID"):
            config.bedrock.model_id = os.getenv("BEDROCK_MODEL_ID")
        if os.getenv("AWS_REGION"):
            config.bedrock.region_name = os.getenv("AWS_REGION")
        elif os.getenv("BEDROCK_REGION"):
            config.bedrock.region_name = os.getenv("BEDROCK_REGION")
        if os.getenv("BEDROCK_TEMPERATURE"):
            config.bedrock.temperature = float(os.getenv("BEDROCK_TEMPERATURE"))
        if os.getenv("BEDROCK_MAX_TOKENS"):
            config.bedrock.max_tokens = int(os.getenv("BEDROCK_MAX_TOKENS"))
        if os.getenv("BEDROCK_STREAMING"):
            config.bedrock.streaming = os.getenv("BEDROCK_STREAMING").lower() == "true"
            
        # Agent configuration from environment
        if os.getenv("AGENT_NAME"):
            config.agent.name = os.getenv("AGENT_NAME")
        if os.getenv("AGENT_DESCRIPTION"):
            config.agent.description = os.getenv("AGENT_DESCRIPTION")
        if os.getenv("SYSTEM_PROMPT"):
            config.agent.system_prompt = os.getenv("SYSTEM_PROMPT")
            
        # API configuration from environment
        if os.getenv("API_HOST"):
            config.api.host = os.getenv("API_HOST")
        if os.getenv("API_PORT"):
            config.api.port = int(os.getenv("API_PORT"))
            
        # Environment configuration from environment
        if os.getenv("ENVIRONMENT_NAME"):
            config.environment.name = os.getenv("ENVIRONMENT_NAME")
        if os.getenv("DEBUG"):
            config.environment.debug = os.getenv("DEBUG").lower() == "true"
        if os.getenv("LOG_LEVEL"):
            config.environment.log_level = os.getenv("LOG_LEVEL")
        if os.getenv("ENABLE_METRICS"):
            config.environment.enable_metrics = os.getenv("ENABLE_METRICS").lower() == "true"
        if os.getenv("RATE_LIMIT_REQUESTS"):
            config.environment.rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS"))
        if os.getenv("MAX_CONCURRENT_CONNECTIONS"):
            config.environment.max_concurrent_connections = int(os.getenv("MAX_CONCURRENT_CONNECTIONS"))
            
        return config
    
    @classmethod
    def from_file(cls, config_path: str) -> "StrandsFlowConfig":
        """Load configuration from a YAML or JSON file."""
        import json
        import yaml
        
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
        with open(config_file, 'r') as f:
            if config_file.suffix.lower() in ['.yml', '.yaml']:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
                
        return cls(**data)
    
    def save_to_file(self, config_path: str) -> None:
        """Save configuration to a YAML or JSON file."""
        import json
        import yaml
        
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            if config_file.suffix.lower() in ['.yml', '.yaml']:
                yaml.dump(self.model_dump(), f, default_flow_style=False)
            else:
                json.dump(self.model_dump(), f, indent=2)


# Default configuration instance
default_config = StrandsFlowConfig()

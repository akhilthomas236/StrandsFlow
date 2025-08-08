"""StrandsFlow agent implementation using Strands SDK."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import structlog
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from strands_tools import (
    calculator,
    current_time,
    file_read,
    file_write,
    python_repl,
    shell
)
from mcp import stdio_client, StdioServerParameters
from mcp.client.sse import sse_client

from .config import StrandsFlowConfig


logger = structlog.get_logger(__name__)


class StrandsFlowAgent:
    """
    StrandsFlow agent that wraps the Strands SDK Agent with additional functionality.
    
    This class provides:
    - Easy configuration management
    - Built-in tool sets
    - MCP server management
    - Production-ready defaults
    """
    
    def __init__(
        self,
        config: Optional[StrandsFlowConfig] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        mcp_servers: Optional[List[Dict[str, Any]]] = None
    ):
        """Initialize StrandsFlow agent."""
        self.config = config or StrandsFlowConfig()
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        
        # Initialize Bedrock model
        self.model = BedrockModel(
            model_id=self.config.bedrock.model_id,
            region_name=self.config.bedrock.region_name,
            temperature=self.config.bedrock.temperature,
            max_tokens=self.config.bedrock.max_tokens,
            streaming=self.config.bedrock.streaming,
        )
        
        # Set up tools
        self.tools = self._setup_tools(tools)
        
        # MCP clients for external tools
        self.mcp_clients: List[MCPClient] = []
        self.mcp_servers = mcp_servers or []
        
        # Initialize the underlying Strands agent
        self.agent: Optional[Agent] = None
        self.is_initialized = False
        
        logger.info(
            "StrandsFlow agent created",
            agent_name=self.config.agent.name,
            model_id=self.config.bedrock.model_id,
            num_builtin_tools=len(self.tools),
            num_mcp_servers=len(self.mcp_servers)
        )
    
    def _setup_tools(self, custom_tools: Optional[List[Any]] = None) -> List[Any]:
        """Set up the default tool set plus any custom tools."""
        # Default StrandsFlow tool set using strands-agents-tools
        default_tools = [
            calculator,  # Mathematical calculations
            current_time,  # Date and time utilities
            file_read,  # File read operations
            file_write,  # File write operations
            python_repl,  # Python code execution
            shell,  # Shell command execution
        ]
        
        if custom_tools:
            default_tools.extend(custom_tools)
        
        return default_tools
    
    async def initialize(self) -> None:
        """Initialize the agent and connect to MCP servers."""
        if self.is_initialized:
            return
        
        try:
            # Initialize MCP clients
            await self._connect_mcp_servers()
            
            # Collect all tools (built-in + MCP)
            all_tools = self.tools.copy()
            
            # Add MCP tools
            for mcp_client in self.mcp_clients:
                mcp_tools = mcp_client.list_tools_sync()
                all_tools.extend(mcp_tools)
            
            # Create the Strands agent with all tools
            self.agent = Agent(
                model=self.model,
                tools=all_tools,
                system_prompt=self.system_prompt
            )
            
            self.is_initialized = True
            logger.info(
                "StrandsFlow agent initialized successfully",
                total_tools=len(all_tools),
                mcp_connections=len(self.mcp_clients)
            )
            
        except Exception as e:
            logger.error("Failed to initialize StrandsFlow agent", error=str(e))
            raise
    
    async def _connect_mcp_servers(self) -> None:
        """Connect to configured MCP servers."""
        for server_config in self.mcp_servers:
            try:
                mcp_client = await self._create_mcp_client(server_config)
                if mcp_client:
                    self.mcp_clients.append(mcp_client)
                    logger.info(
                        "Connected to MCP server",
                        server_name=server_config.get("name", "unknown"),
                        transport=server_config.get("transport", "unknown")
                    )
            except Exception as e:
                logger.error(
                    "Failed to connect to MCP server",
                    server_config=server_config,
                    error=str(e)
                )
    
    async def _create_mcp_client(self, config: Dict[str, Any]) -> Optional[MCPClient]:
        """Create an MCP client based on configuration."""
        transport = config.get("transport", "stdio")
        
        if transport == "stdio":
            command = config.get("command", "uvx")
            args = config.get("args", [])
            
            return MCPClient(lambda: stdio_client(
                StdioServerParameters(command=command, args=args)
            ))
        
        elif transport == "sse":
            url = config.get("url", "http://localhost:8000/sse")
            return MCPClient(lambda: sse_client(url))
        
        else:
            logger.warning(f"Unsupported MCP transport: {transport}")
            return None
    
    async def chat(self, message: str) -> str:
        """Send a message to the agent and get a response."""
        if not self.is_initialized:
            await self.initialize()
        
        if not self.agent:
            raise RuntimeError("Agent not properly initialized")
        
        try:
            # Use the MCP clients in context
            if self.mcp_clients:
                # Use context manager for MCP connections
                async with asyncio.gather(*[
                    mcp_client.__aenter__() for mcp_client in self.mcp_clients
                ]):
                    result = self.agent(message)
                    return result.message
            else:
                # No MCP servers, use agent directly
                result = self.agent(message)
                return result.message
                
        except Exception as e:
            logger.error("Error processing message", error=str(e))
            raise
    
    async def chat_async(self, message: str):
        """Async chat with streaming support."""
        if not self.is_initialized:
            await self.initialize()
        
        if not self.agent:
            raise RuntimeError("Agent not properly initialized")
        
        try:
            if self.mcp_clients:
                # Use context manager for MCP connections
                async with asyncio.gather(*[
                    mcp_client.__aenter__() for mcp_client in self.mcp_clients
                ]):
                    async for event in self.agent.stream_async(message):
                        yield event
            else:
                # No MCP servers, use agent directly
                async for event in self.agent.stream_async(message):
                    yield event
                
        except Exception as e:
            logger.error("Error in async chat", error=str(e))
            raise
    
    def add_tool(self, tool: Any) -> None:
        """Add a custom tool to the agent."""
        self.tools.append(tool)
        if self.is_initialized:
            logger.warning("Tool added after initialization. Re-initialize to use new tool.")
    
    async def add_mcp_server(
        self,
        name: str,
        transport: str,
        **kwargs
    ) -> None:
        """Add an MCP server configuration."""
        server_config = {
            "name": name,
            "transport": transport,
            **kwargs
        }
        self.mcp_servers.append(server_config)
        
        if self.is_initialized:
            # Try to connect to the new server
            mcp_client = await self._create_mcp_client(server_config)
            if mcp_client:
                self.mcp_clients.append(mcp_client)
                logger.info(f"Added MCP server: {name}")
    
    async def discover_mcp_servers(self) -> List[Dict[str, Any]]:
        """Discover MCP servers from configured paths."""
        discovered_servers = []
        
        if not self.config.mcp.auto_discover:
            return discovered_servers
        
        for discovery_path in self.config.mcp.discovery_paths:
            try:
                path = Path(discovery_path).expanduser()
                if path.exists() and path.is_dir():
                    for server_file in path.glob("*.json"):
                        try:
                            with open(server_file, 'r') as f:
                                server_config = json.load(f)
                                server_config['source'] = str(server_file)
                                discovered_servers.append(server_config)
                                logger.info(f"Discovered MCP server: {server_config.get('name', server_file.name)}")
                        except Exception as e:
                            logger.warning(f"Failed to load MCP server config {server_file}: {e}")
            except Exception as e:
                logger.warning(f"Failed to scan discovery path {discovery_path}: {e}")
        
        return discovered_servers
    
    async def add_mcp_server_from_config(self, server_config: Dict[str, Any]) -> bool:
        """Add an MCP server from configuration."""
        try:
            name = server_config.get('name', 'unknown')
            transport = server_config.get('transport', 'stdio')
            
            if transport == 'stdio':
                command = server_config.get('command', [])
                if not command:
                    logger.error(f"MCP server {name} missing command")
                    return False
                
                mcp_client = await self._create_mcp_client({
                    'name': name,
                    'transport': transport,
                    'command': command,
                    'args': server_config.get('args', []),
                    'env': server_config.get('env', {})
                })
                
                if mcp_client:
                    self.mcp_clients.append(mcp_client)
                    logger.info(f"Added MCP server: {name}")
                    return True
                    
            else:
                logger.warning(f"Unsupported MCP transport for {name}: {transport}")
                
        except Exception as e:
            logger.error(f"Failed to add MCP server: {e}")
            
        return False
    
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt for StrandsFlow."""
        return f"""You are {self.config.agent.name}, a helpful AI assistant powered by StrandsFlow and the Strands Agents SDK.

{self.config.agent.description}

You have access to various tools and can help users with:
- Mathematical calculations and data analysis
- File system operations (reading, writing, organizing files)
- Python code execution and development
- Shell/terminal command execution
- Current date and time information
- Web requests and API interactions (via MCP extensions)

Key capabilities:
- Built on the production-ready Strands Agents SDK
- AWS Bedrock integration for reliable AI responses
- Extensible tool ecosystem via Model Context Protocol (MCP)
- Real-time streaming responses
- Comprehensive observability and monitoring

Always be helpful, accurate, and concise in your responses. When using tools:
1. Explain what you're doing and why
2. Show the results clearly
3. Handle errors gracefully
4. Ask for clarification if needed

If you're unsure about something, ask for clarification rather than making assumptions.

How can I assist you today?"""
    
    async def shutdown(self) -> None:
        """Shutdown the agent and cleanup resources."""
        logger.info("Shutting down StrandsFlow agent")
        
        # Close MCP connections
        for mcp_client in self.mcp_clients:
            try:
                await mcp_client.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing MCP client: {e}")
        
        self.mcp_clients.clear()
        self.is_initialized = False
        
        logger.info("StrandsFlow agent shutdown complete")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics and status."""
        return {
            "is_initialized": self.is_initialized,
            "model_id": self.config.bedrock.model_id,
            "num_tools": len(self.tools),
            "num_mcp_servers": len(self.mcp_servers),
            "num_mcp_connections": len(self.mcp_clients),
            "agent_name": self.config.agent.name,
        }

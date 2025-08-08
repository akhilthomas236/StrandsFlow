"""A2A (Agent-to-Agent) server implementation for StrandsFlow."""

import asyncio
import logging
from typing import Any, Dict, Optional

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

try:
    from a2a.server.apps import A2AFastAPIApplication
    A2A_AVAILABLE = True
except ImportError:
    A2A_AVAILABLE = False
    A2AFastAPIApplication = None

from strands import Agent

from ..core.agent import StrandsFlowAgent
from ..core.config import StrandsFlowConfig


"""A2A (Agent-to-Agent) communication implementation for StrandsFlow."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from strands import Agent, tool
from strands_tools import use_agent
from strands_tools.a2a_client import A2AClientToolProvider

from ..core.agent import StrandsFlowAgent


@dataclass
class AgentCard:
    """Agent card for A2A discovery."""
    name: str
    description: str
    endpoint: str
    capabilities: List[str]
    model: str
    tools: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "endpoint": self.endpoint,
            "capabilities": self.capabilities,
            "model": self.model,
            "tools": self.tools
        }


class AgentAsToolWrapper:
    """Wrapper to expose an agent as a tool for other agents."""
    
    def __init__(self, agent: StrandsFlowAgent, name: str, description: str):
        """Initialize agent wrapper."""
        self.agent = agent
        self.name = name
        self.description = description
    
    async def __call__(self, query: str) -> Dict[str, Any]:
        """Call the agent with a query."""
        try:
            if not self.agent.is_initialized:
                await self.agent.initialize()
            
            response = await self.agent.chat(query)
            return {
                "status": "success",
                "content": response,
                "agent": self.name,
                "model": self.agent.config.bedrock.model_id
            }
        except Exception as e:
            logger.error(f"Error in agent {self.name}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "agent": self.name
            }
    
    def create_tool(self):
        """Create a tool function for this agent."""
        async def agent_tool(query: str) -> str:
            f"""Ask {self.name}: {self.description}"""
            result = await self(query)
            if result["status"] == "success":
                return result["content"]
            else:
                return f"Error: {result['error']}"
        
        agent_tool.__name__ = f"ask_{self.name.lower().replace(' ', '_')}"
        agent_tool.__doc__ = f"Ask {self.name}: {self.description}"
        
        return tool(agent_tool)


class A2AServer:
    """
    A2A Server implementation for StrandsFlow agents.
    
    This provides a simplified A2A pattern where agents can be exposed
    as tools for other agents to use.
    """
    
    def __init__(
        self,
        agent: StrandsFlowAgent,
        name: Optional[str] = None,
        description: Optional[str] = None
    ):
        """Initialize A2A server for a StrandsFlow agent."""
        self.agent = agent
        self.name = name or agent.config.agent.name
        self.description = description or agent.config.agent.description
        
        # Create wrapper
        self.wrapper = AgentAsToolWrapper(agent, self.name, self.description)
        
        # Create agent card
        self.card = AgentCard(
            name=self.name,
            description=self.description,
            endpoint=f"local://{self.name}",
            capabilities=["chat", "streaming", "tools"],
            model=agent.config.bedrock.model_id,
            tools=[tool.__name__ if hasattr(tool, '__name__') else str(tool) for tool in agent.tools]
        )
        
        logger.info(
            "A2A server initialized",
            agent_name=self.name,
            model=self.card.model
        )
    
    def get_tool(self):
        """Get the tool representation of this agent."""
        return self.wrapper.create_tool()
    
    def get_card(self) -> Dict[str, Any]:
        """Get the agent card information."""
        return self.card.to_dict()
    
    async def call(self, query: str) -> Dict[str, Any]:
        """Direct call to the agent."""
        return await self.wrapper(query)


class A2AClient:
    """A2A Client for discovering and communicating with other agents."""
    
    def __init__(self, known_agents: Optional[List[str]] = None):
        """Initialize A2A client."""
        self.known_agents = known_agents or []
        self.discovered_agents: Dict[str, AgentCard] = {}
        
        # Initialize A2A client tool provider if available
        try:
            self.tool_provider = A2AClientToolProvider(known_agent_urls=self.known_agents)
            self.has_external_a2a = True
        except Exception as e:
            logger.warning(f"External A2A client not available: {e}")
            self.tool_provider = None
            self.has_external_a2a = False
    
    def register_agent(self, server: A2AServer):
        """Register a local agent."""
        self.discovered_agents[server.name] = server.card
        logger.info(f"Registered local agent: {server.name}")
    
    def get_tools(self) -> List[Any]:
        """Get all available A2A tools."""
        tools = []
        
        # Add external A2A tools if available
        if self.has_external_a2a and self.tool_provider:
            try:
                tools.extend(self.tool_provider.tools)
            except Exception as e:
                logger.warning(f"Error getting external A2A tools: {e}")
        
        return tools
    
    def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """List all discovered agents."""
        return {name: card.to_dict() for name, card in self.discovered_agents.items()}


class A2AServerManager:
    """Manager for multiple A2A servers and client."""
    
    def __init__(self):
        """Initialize the A2A server manager."""
        self.servers: Dict[str, A2AServer] = {}
        self.client = A2AClient()
        
        logger.info("A2A server manager initialized")
    
    def add_agent(
        self,
        agent: StrandsFlowAgent,
        name: Optional[str] = None
    ) -> A2AServer:
        """Add an agent as an A2A server."""
        server_name = name or agent.config.agent.name
        
        if server_name in self.servers:
            raise ValueError(f"A2A server '{server_name}' already exists")
        
        # Create A2A server
        a2a_server = A2AServer(
            agent=agent,
            name=server_name
        )
        
        # Store and register
        self.servers[server_name] = a2a_server
        self.client.register_agent(a2a_server)
        
        logger.info(
            "Added A2A server",
            server_name=server_name,
            model=a2a_server.card.model
        )
        
        return a2a_server
    
    def remove_agent(self, name: str) -> bool:
        """Remove an A2A server."""
        if name not in self.servers:
            return False
        
        del self.servers[name]
        if name in self.client.discovered_agents:
            del self.client.discovered_agents[name]
        
        logger.info("Removed A2A server", server_name=name)
        return True
    
    def get_agent_tools(self, exclude: Optional[List[str]] = None) -> List[Any]:
        """Get tools for all registered agents."""
        exclude = exclude or []
        tools = []
        
        for name, server in self.servers.items():
            if name not in exclude:
                tools.append(server.get_tool())
        
        # Add external A2A tools
        tools.extend(self.client.get_tools())
        
        return tools
    
    def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """List all A2A servers."""
        return self.client.list_agents()
    
    def get_agent(self, name: str) -> Optional[A2AServer]:
        """Get an A2A server by name."""
        return self.servers.get(name)
    
    async def call_agent(self, name: str, query: str) -> Dict[str, Any]:
        """Call a specific agent directly."""
        if name not in self.servers:
            return {"status": "error", "error": f"Agent '{name}' not found"}
        
        return await self.servers[name].call(query)

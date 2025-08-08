"""FastAPI application for StrandsFlow."""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import structlog

from ..core.agent import StrandsFlowAgent
from ..core.config import StrandsFlowConfig

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Pydantic models for API
class MessageRequest(BaseModel):
    content: str
    session_id: Optional[str] = None

class MessageResponse(BaseModel):
    response: str
    session_id: str
    conversation_id: str

class SessionInfo(BaseModel):
    session_id: str
    conversation_count: int
    created_at: str

class AgentInfo(BaseModel):
    name: str
    description: str
    version: str
    model_id: str
    max_conversation_turns: int

class HealthResponse(BaseModel):
    status: str
    version: str
    agent_ready: bool

# Global variables
config: Optional[StrandsFlowConfig] = None
agent: Optional[StrandsFlowAgent] = None
sessions: Dict[str, Dict[str, Any]] = {}

# FastAPI app
app = FastAPI(
    title="StrandsFlow API",
    description="AI Agent Platform built on Strands Agents SDK with AWS Bedrock and MCP integration",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware immediately
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will be updated from config during startup
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_config() -> StrandsFlowConfig:
    """Get the global config instance."""
    global config
    if config is None:
        # Try to load from file first, then fall back to environment
        config_file = "strandsflow.yaml"
        if os.path.exists(config_file):
            config = StrandsFlowConfig.from_file(config_file)
        else:
            config = StrandsFlowConfig.from_env()
    return config

def get_agent() -> StrandsFlowAgent:
    """Get the global agent instance."""
    global agent
    if agent is None:
        agent_config = get_config()
        agent = StrandsFlowAgent(agent_config)
    return agent

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    try:
        logger.info("Starting StrandsFlow API...")
        
        # Load configuration
        app_config = get_config()
        logger.info("Configuration loaded", config=app_config.model_dump())
        
        # Initialize agent
        app_agent = get_agent()
        logger.info("Agent initialized", agent_name=app_agent.config.agent.name)
        
        logger.info("StrandsFlow API started successfully")
        
    except Exception as e:
        logger.error("Failed to start StrandsFlow API", error=str(e))
        raise

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        app_agent = get_agent()
        agent_ready = True
    except Exception:
        agent_ready = False
    
    return HealthResponse(
        status="healthy" if agent_ready else "degraded",
        version="0.1.0",
        agent_ready=agent_ready
    )

@app.get("/agent/info", response_model=AgentInfo)
async def get_agent_info():
    """Get agent information."""
    try:
        app_agent = get_agent()
        return AgentInfo(
            name=app_agent.config.agent.name,
            description=app_agent.config.agent.description,
            version="0.1.0",
            model_id=app_agent.config.bedrock.model_id,
            max_conversation_turns=app_agent.config.agent.max_conversation_turns
        )
    except Exception as e:
        logger.error("Failed to get agent info", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get agent info: {str(e)}")

@app.post("/chat", response_model=MessageResponse)
async def chat_with_agent(request: MessageRequest):
    """Send a message to the agent and get a response."""
    try:
        app_agent = get_agent()
        
        # Use provided session_id or create new one
        session_id = request.session_id or str(uuid4())
        
        # Initialize session if new
        if session_id not in sessions:
            sessions[session_id] = {
                "conversation_count": 0,
                "created_at": "2025-08-08T00:00:00Z",
                "messages": []
            }
        
        # Process the message
        response_text = await app_agent.chat(request.content)
        
        # Update session
        sessions[session_id]["conversation_count"] += 1
        sessions[session_id]["messages"].append({
            "user": request.content,
            "agent": response_text,
            "timestamp": "2025-08-08T00:00:00Z"
        })
        
        return MessageResponse(
            response=response_text,
            session_id=session_id,
            conversation_id=str(uuid4())
        )
        
    except Exception as e:
        logger.error("Failed to process chat message", error=str(e), session_id=request.session_id)
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@app.get("/sessions", response_model=List[SessionInfo])
async def list_sessions():
    """List all active sessions."""
    return [
        SessionInfo(
            session_id=session_id,
            conversation_count=session_data["conversation_count"],
            created_at=session_data["created_at"]
        )
        for session_id, session_data in sessions.items()
    ]

@app.get("/sessions/{session_id}", response_model=Dict[str, Any])
async def get_session(session_id: str):
    """Get session details."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        **sessions[session_id]
    }

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del sessions[session_id]
    return {"message": f"Session {session_id} deleted successfully"}

@app.delete("/sessions")
async def clear_all_sessions():
    """Clear all sessions."""
    sessions.clear()
    return {"message": "All sessions cleared successfully"}

# Export the app for ASGI servers
__all__ = ["app"]

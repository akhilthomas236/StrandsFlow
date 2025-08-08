"""FastAPI application for StrandsFlow."""

import asyncio
import logging
import os
import json
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
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

class MetricsResponse(BaseModel):
    total_sessions: int
    active_connections: int
    total_messages: int
    uptime_seconds: float
    agent_metrics: Dict[str, Any]

# Global variables
config: Optional[StrandsFlowConfig] = None
agent: Optional[StrandsFlowAgent] = None
sessions: Dict[str, Dict[str, Any]] = {}

# Metrics tracking
import time
start_time = time.time()
total_messages_processed = 0

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.session_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if session_id:
            if session_id not in self.session_connections:
                self.session_connections[session_id] = []
            self.session_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: str = None):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if session_id and session_id in self.session_connections:
            if websocket in self.session_connections[session_id]:
                self.session_connections[session_id].remove(websocket)
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast_to_session(self, message: str, session_id: str):
        if session_id in self.session_connections:
            for connection in self.session_connections[session_id]:
                await connection.send_text(message)

manager = ConnectionManager()

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
    global total_messages_processed
    
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
        
        # Update session and metrics
        sessions[session_id]["conversation_count"] += 1
        total_messages_processed += 1
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

@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get system metrics for monitoring."""
    try:
        app_agent = get_agent()
        agent_metrics = app_agent.get_metrics()
    except Exception:
        agent_metrics = {}
    
    return MetricsResponse(
        total_sessions=len(sessions),
        active_connections=len(manager.active_connections),
        total_messages=total_messages_processed,
        uptime_seconds=time.time() - start_time,
        agent_metrics=agent_metrics
    )

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat."""
    global total_messages_processed
    
    await manager.connect(websocket, session_id)
    
    # Initialize session if new
    if session_id not in sessions:
        sessions[session_id] = {
            "conversation_count": 0,
            "created_at": "2025-08-08T00:00:00Z",
            "messages": []
        }
        
    try:
        await websocket.send_text(json.dumps({
            "type": "connection",
            "message": f"Connected to session {session_id}",
            "session_id": session_id
        }))
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "chat":
                user_message = message_data.get("message", "")
                
                # Send typing indicator
                await websocket.send_text(json.dumps({
                    "type": "typing",
                    "message": "Agent is typing...",
                    "session_id": session_id
                }))
                
                try:
                    # Get agent response with streaming
                    app_agent = get_agent()
                    
                    # Use chat_async for streaming
                    response_chunks = []
                    async for chunk in app_agent.chat_async(user_message):
                        chunk_text = str(chunk)
                        response_chunks.append(chunk_text)
                        
                        # Send streaming chunk
                        await websocket.send_text(json.dumps({
                            "type": "chunk",
                            "content": chunk_text,
                            "session_id": session_id
                        }))
                    
                    # Final complete response
                    full_response = "".join(response_chunks)
                    
                    # Update session
                    sessions[session_id]["conversation_count"] += 1
                    total_messages_processed += 1
                    sessions[session_id]["messages"].append({
                        "user": user_message,
                        "agent": full_response,
                        "timestamp": "2025-08-08T00:00:00Z"
                    })
                    
                    # Send completion message
                    await websocket.send_text(json.dumps({
                        "type": "complete",
                        "message": full_response,
                        "session_id": session_id,
                        "conversation_count": sessions[session_id]["conversation_count"]
                    }))
                    
                except Exception as e:
                    logger.error("Error in WebSocket chat", error=str(e))
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Error: {str(e)}",
                        "session_id": session_id
                    }))
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        logger.info("WebSocket disconnected", session_id=session_id)
    except Exception as e:
        logger.error("WebSocket error", error=str(e), session_id=session_id)
        manager.disconnect(websocket, session_id)

# Export the app for ASGI servers
__all__ = ["app"]

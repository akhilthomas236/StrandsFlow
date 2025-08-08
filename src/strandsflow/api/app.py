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

# Multi-agent API endpoints
try:
    from ..multiagent import (
        Orchestrator, WorkflowType, SpecialistPool, create_predefined_pool,
        WorkflowManager, A2AServerManager
    )
    MULTIAGENT_AVAILABLE = True
except ImportError:
    MULTIAGENT_AVAILABLE = False
    logger.warning("Multi-agent features not available - missing dependencies")

# Multi-agent Pydantic models
if MULTIAGENT_AVAILABLE:
    class MultiAgentTask(BaseModel):
        task: str
        workflow_type: str = "conditional"
        agents: Optional[List[str]] = None
        
    class MultiAgentResponse(BaseModel):
        status: str
        workflow_type: str
        results: Dict[str, Any]
        execution_time: Optional[float] = None
        
    class WorkflowExecuteRequest(BaseModel):
        workflow_name: str
        inputs: Dict[str, Any]
        
    class WorkflowExecuteResponse(BaseModel):
        execution_id: str
        status: str
        
    class SpecialistCreateRequest(BaseModel):
        name: str
        role: str
        description: str
        system_prompt: str
        capabilities: List[str]
        model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
        temperature: float = 0.7

# Global multi-agent instances
orchestrator: Optional[Orchestrator] = None
specialist_pool: Optional[SpecialistPool] = None
workflow_manager: Optional[WorkflowManager] = None
a2a_manager: Optional[A2AServerManager] = None

async def get_orchestrator() -> Orchestrator:
    """Get or create the global orchestrator instance."""
    global orchestrator, specialist_pool, a2a_manager
    
    if not MULTIAGENT_AVAILABLE:
        raise HTTPException(status_code=501, detail="Multi-agent features not available")
    
    if orchestrator is None:
        # Initialize specialist pool
        if specialist_pool is None:
            specialist_pool = await create_predefined_pool(get_config())
            await specialist_pool.initialize_all()
        
        # Initialize A2A manager
        if a2a_manager is None:
            a2a_manager = A2AServerManager()
        
        # Create orchestrator
        orchestrator = Orchestrator(a2a_manager=a2a_manager)
        
        # Add specialists to orchestrator
        for name, agent in specialist_pool.specialists.items():
            config = specialist_pool.configs[name]
            orchestrator.add_specialist(name, agent, config.role, config.capabilities)
        
        # Create orchestrator agent
        orchestrator.create_orchestrator_agent()
        
        logger.info("Multi-agent orchestrator initialized")
    
    return orchestrator

async def get_workflow_manager() -> WorkflowManager:
    """Get or create the global workflow manager instance."""
    global workflow_manager
    
    if not MULTIAGENT_AVAILABLE:
        raise HTTPException(status_code=501, detail="Multi-agent features not available")
    
    if workflow_manager is None:
        orch = await get_orchestrator()
        workflow_manager = WorkflowManager(orch, specialist_pool)
        logger.info("Workflow manager initialized")
    
    return workflow_manager

# Multi-agent endpoints
if MULTIAGENT_AVAILABLE:
    
    @app.get("/api/v1/multiagent/status")
    async def get_multiagent_status():
        """Get multi-agent system status."""
        try:
            orch = await get_orchestrator()
            wf_mgr = await get_workflow_manager()
            
            return {
                "status": "ready",
                "orchestrator": orch.get_metrics(),
                "specialist_pool": specialist_pool.get_metrics() if specialist_pool else {},
                "workflow_manager": {
                    "workflows": len(wf_mgr.workflows),
                    "executions": len(wf_mgr.executions)
                },
                "a2a_manager": {
                    "servers": len(a2a_manager.servers) if a2a_manager else 0
                }
            }
        except Exception as e:
            logger.error(f"Error getting multi-agent status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/v1/multiagent/execute", response_model=MultiAgentResponse)
    async def execute_multiagent_task(request: MultiAgentTask):
        """Execute a task using multi-agent orchestration."""
        try:
            orch = await get_orchestrator()
            
            # Parse workflow type
            workflow_type = WorkflowType(request.workflow_type.lower())
            
            start_time = time.time()
            result = await orch.execute_workflow(
                task=request.task,
                workflow_type=workflow_type,
                agents=request.agents
            )
            execution_time = time.time() - start_time
            
            return MultiAgentResponse(
                status="success",
                workflow_type=request.workflow_type,
                results=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Error executing multi-agent task: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v1/multiagent/specialists")
    async def list_specialists():
        """List all available specialist agents."""
        try:
            orch = await get_orchestrator()
            return specialist_pool.list_specialists() if specialist_pool else {}
        except Exception as e:
            logger.error(f"Error listing specialists: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/v1/multiagent/specialists")
    async def create_specialist(request: SpecialistCreateRequest):
        """Create a new specialist agent."""
        try:
            if not specialist_pool:
                raise HTTPException(status_code=500, detail="Specialist pool not initialized")
            
            from ..multiagent.specialist_pool import SpecialistConfig
            
            config = SpecialistConfig(
                name=request.name,
                role=request.role,
                description=request.description,
                system_prompt=request.system_prompt,
                capabilities=request.capabilities,
                model_id=request.model_id,
                temperature=request.temperature
            )
            
            specialist = await specialist_pool.add_specialist(config, get_config())
            await specialist.initialize()
            
            # Add to orchestrator if available
            if orchestrator:
                orchestrator.add_specialist(request.name, specialist, request.role, request.capabilities)
            
            return {"status": "success", "message": f"Specialist '{request.name}' created"}
            
        except Exception as e:
            logger.error(f"Error creating specialist: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v1/multiagent/workflows")
    async def list_workflows():
        """List all available workflows."""
        try:
            wf_mgr = await get_workflow_manager()
            return wf_mgr.list_workflows()
        except Exception as e:
            logger.error(f"Error listing workflows: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/v1/multiagent/workflows/execute", response_model=WorkflowExecuteResponse)
    async def execute_workflow(request: WorkflowExecuteRequest):
        """Execute a predefined workflow."""
        try:
            wf_mgr = await get_workflow_manager()
            
            execution_id = await wf_mgr.execute_workflow(
                workflow_name=request.workflow_name,
                inputs=request.inputs
            )
            
            return WorkflowExecuteResponse(
                execution_id=execution_id,
                status="started"
            )
            
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v1/multiagent/workflows/{execution_id}")
    async def get_workflow_status(execution_id: str):
        """Get workflow execution status."""
        try:
            wf_mgr = await get_workflow_manager()
            execution = wf_mgr.get_execution_status(execution_id)
            
            if not execution:
                raise HTTPException(status_code=404, detail="Workflow execution not found")
            
            return {
                "execution_id": execution_id,
                "workflow_name": execution.workflow_name,
                "status": execution.status.value,
                "current_step": execution.current_step,
                "results": execution.results,
                "error": execution.error,
                "start_time": execution.start_time,
                "end_time": execution.end_time
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting workflow status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v1/multiagent/workflows/executions")
    async def list_workflow_executions():
        """List all workflow executions."""
        try:
            wf_mgr = await get_workflow_manager()
            return wf_mgr.list_executions()
        except Exception as e:
            logger.error(f"Error listing workflow executions: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v1/multiagent/a2a/agents")
    async def list_a2a_agents():
        """List all A2A agents."""
        try:
            orch = await get_orchestrator()
            return a2a_manager.list_agents() if a2a_manager else {}
        except Exception as e:
            logger.error(f"Error listing A2A agents: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Add shutdown handler for multi-agent resources
@app.on_event("shutdown")
async def shutdown_multiagent():
    """Cleanup multi-agent resources on shutdown."""
    if specialist_pool:
        await specialist_pool.shutdown_all()
        logger.info("Specialist pool shutdown complete")
    
    if a2a_manager:
        # No explicit shutdown needed for our simplified A2A implementation
        logger.info("A2A manager shutdown complete")

# Export the app for ASGI servers
__all__ = ["app"]

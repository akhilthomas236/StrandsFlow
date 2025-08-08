# StrandsFlow

🚀 **AI Agent Platform built on Strands Agents SDK**

StrandsFlow is a production-ready AI agent platform that extends the [Strands Agents SDK](https://strandsagents.com) with AWS Bedrock integration and Model Context Protocol (MCP) support.

## ✨ Features

- **🏗️ Built on Strands SDK**: Production-ready agent framework with official Strands Agents SDK
- **☁️ AWS Bedrock Integration**: Native support for Claude 3 Haiku, Sonnet, and other Bedrock models
- **🔧 Rich Tool Ecosystem**: File operations, Python execution, shell commands, calculations via strands-agents-tools
- **🌐 REST API**: FastAPI-based endpoints for agent interactions with async/streaming support
- **⚡ Real-time Streaming**: WebSocket support for real-time conversations and streaming responses
- **🔌 MCP Protocol**: Extensible tool ecosystem via Model Context Protocol with auto-discovery
- **📊 Observability**: Built-in structured logging, metrics, and health monitoring
- **🖥️ CLI Interface**: Rich command-line interface with Typer and Rich
- **⚙️ Configuration Management**: Flexible config with environment variables, files (JSON/YAML), and profiles
- **🤖 Custom Agents**: Easy creation of specialized agents via configuration or code
- **🔒 Production Ready**: Error handling, connection management, and scalable architecture

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI
pip install strandsflow

# Or install from source
git clone https://github.com/akhilthomas236/StrandsFlow.git
cd StrandsFlow
pip install -e .
```

### AWS Configuration

Configure AWS credentials for Bedrock access:

```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-west-2
```

**Note**: Ensure you have access to Claude models in Amazon Bedrock console.

### CLI Usage

```bash
# Initialize configuration
strandsflow init

# Start interactive chat
strandsflow chat

# View configuration
strandsflow config --show

# Start API server
strandsflow server

# Check version
strandsflow version
```

### Basic Usage

#### CLI Interface

```bash
# Test the installation
strandsflow test

# Get platform information
strandsflow info

# Chat with an agent
strandsflow chat "What's 15 * 23?"

# Start the API server
strandsflow server
```

#### Python API

```python
from strands import Agent
from strands.models import BedrockModel
from strands_tools import calculator, current_time, file_read

# Create agent with Bedrock
model = BedrockModel(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    region_name="us-west-2"
)

agent = Agent(
    model=model,
    tools=[calculator, current_time, file_read]
)

# Chat with agent
result = agent("What's the current time and what's 2+2?")
print(result.message)
```

#### REST API

Start the server:
```bash
strandsflow server
```

Then access the API:
```bash
# Create an agent
curl -X POST "http://localhost:8000/api/v1/agents" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Agent"}'

# Chat with agent
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello! What can you do?"}'
```

API documentation available at: http://localhost:8000/docs

## 🤖 Creating Custom Agents

StrandsFlow provides multiple ways to create and configure custom agents for your specific use cases.

### Method 1: Configuration-Based Agents

The easiest way to create a custom agent is using a YAML configuration file:

#### 1. Create Agent Configuration

Create a new configuration file (e.g., `my_agent.yaml`):

```yaml
agent:
  name: "Code Review Assistant"
  description: "AI agent specialized in code review and analysis"
  system_prompt: |
    You are an expert code reviewer and software engineer. 
    Your role is to:
    - Analyze code for bugs, security issues, and performance problems
    - Suggest improvements and best practices
    - Explain complex code concepts clearly
    - Follow industry standards and conventions
  enable_memory: true
  max_conversation_turns: 100

bedrock:
  model_id: "anthropic.claude-3-sonnet-20240229-v1:0"
  region_name: "us-west-2"
  temperature: 0.3
  max_tokens: 4096
  streaming: true

api:
  host: "0.0.0.0"
  port: 8001
  cors_origins: ["*"]

environment:
  name: "production"
  log_level: "INFO"
  debug: false
  enable_metrics: true

mcp:
  auto_discover: true
  servers:
    # Add custom MCP servers here
    code_analyzer:
      command: ["node", "/path/to/code-analyzer-server"]
      transport: "stdio"
```

#### 2. Launch Your Custom Agent

```bash
# Using CLI with custom config
strandsflow server --config my_agent.yaml

# Or specify config via environment
export STRANDSFLOW_CONFIG=my_agent.yaml
strandsflow server
```

#### 3. Configuration Options

**Agent Settings:**
- `name`: Display name for your agent
- `description`: Brief description of agent capabilities
- `system_prompt`: Custom system prompt defining agent behavior
- `enable_memory`: Enable conversation memory (default: true)
- `max_conversation_turns`: Maximum conversation history (default: 50)

**Model Settings:**
- `model_id`: AWS Bedrock model identifier
- `temperature`: Creativity level (0.0-1.0)
- `max_tokens`: Maximum response length
- `streaming`: Enable real-time response streaming

**API Settings:**
- `host`: Server host address
- `port`: Server port number
- `cors_origins`: Allowed CORS origins

### Method 2: Programmatic Agent Creation

For more advanced use cases, create agents programmatically:

#### Basic Custom Agent

```python
from strands import Agent
from strands.models import BedrockModel
from strands_tools import calculator, file_read, python_repl
from strandsflow.core.config import Config

# Load configuration
config = Config.from_file("my_agent.yaml")

# Create model with custom settings
model = BedrockModel(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    region_name="us-west-2",
    temperature=0.3,
    max_tokens=4096
)

# Create agent with custom tools
agent = Agent(
    model=model,
    tools=[calculator, file_read, python_repl],
    instructions="""
    You are a specialized data analysis assistant.
    Help users analyze data, create visualizations, and derive insights.
    Always explain your reasoning and provide clear, actionable recommendations.
    """
)

# Use the agent
response = agent("Analyze the sales data in sales.csv and create a summary report")
print(response.message)
```

#### Advanced Custom Agent with Tool Selection

```python
from strands import Agent
from strands.models import BedrockModel
from strands_tools import *

class CustomDataAgent:
    def __init__(self, config_path: str = None):
        self.config = Config.from_file(config_path) if config_path else Config()
        self.model = self._create_model()
        self.agent = self._create_agent()
    
    def _create_model(self):
        return BedrockModel(
            model_id=self.config.bedrock.model_id,
            region_name=self.config.bedrock.region_name,
            temperature=self.config.bedrock.temperature,
            max_tokens=self.config.bedrock.max_tokens
        )
    
    def _create_agent(self):
        # Select tools based on agent purpose
        data_tools = [
            calculator,
            python_repl,
            file_read,
            file_write,
            current_time
        ]
        
        return Agent(
            model=self.model,
            tools=data_tools,
            instructions=self.config.agent.system_prompt
        )
    
    async def chat(self, message: str) -> str:
        response = await self.agent.run_async(message)
        return response.message
    
    def chat_sync(self, message: str) -> str:
        response = self.agent(message)
        return response.message

# Usage
agent = CustomDataAgent("data_agent.yaml")
result = agent.chat_sync("What's the average of these numbers: 10, 20, 30, 40?")
```

### Method 3: Extending with Custom Tools

Create your own tools for specialized functionality:

#### Custom Tool Example

```python
from strands.tools import Tool
from pydantic import BaseModel, Field
import requests

class WeatherRequest(BaseModel):
    city: str = Field(description="City name to get weather for")

def get_weather(city: str) -> str:
    """Get current weather for a city."""
    # Implementation here
    api_key = "your_api_key"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
    response = requests.get(url)
    data = response.json()
    return f"Weather in {city}: {data['weather'][0]['description']}"

# Create tool
weather_tool = Tool(
    name="get_weather",
    description="Get current weather information for any city",
    function=get_weather,
    parameters=WeatherRequest
)

# Add to agent
agent = Agent(
    model=model,
    tools=[weather_tool, calculator, current_time],
    instructions="You are a helpful assistant with access to weather information."
)
```

#### Custom MCP Server Integration

```python
# Add to your agent config
mcp:
  servers:
    weather_service:
      command: ["python", "/path/to/weather_mcp_server.py"]
      transport: "stdio"
      args: ["--api-key", "${WEATHER_API_KEY}"]
    
    database_tools:
      command: ["node", "/path/to/db_server.js"]
      transport: "stdio"
      env:
        DB_CONNECTION_STRING: "${DATABASE_URL}"
```

### Method 4: Specialized Agent Templates

#### Customer Support Agent

```yaml
agent:
  name: "Customer Support Assistant"
  system_prompt: |
    You are a friendly and professional customer support representative.
    - Always be helpful, patient, and understanding
    - Ask clarifying questions when needed
    - Provide step-by-step solutions
    - Escalate complex issues appropriately
    - Follow up to ensure customer satisfaction
  
bedrock:
  model_id: "anthropic.claude-3-haiku-20240307-v1:0"
  temperature: 0.5
```

#### Technical Documentation Agent

```yaml
agent:
  name: "Documentation Assistant"
  system_prompt: |
    You are a technical writing expert specializing in clear, comprehensive documentation.
    - Write clear, concise explanations
    - Use proper formatting and structure
    - Include practical examples
    - Consider different skill levels
    - Maintain consistency in tone and style

mcp:
  servers:
    code_analyzer:
      command: ["npx", "@modelcontextprotocol/server-everything"]
      transport: "stdio"
```

#### Data Analysis Agent

```yaml
agent:
  name: "Data Analyst"
  system_prompt: |
    You are an expert data analyst with strong statistical and visualization skills.
    - Perform thorough data exploration
    - Create meaningful visualizations
    - Provide statistical insights
    - Suggest data-driven recommendations
    - Explain findings in business terms

bedrock:
  model_id: "anthropic.claude-3-sonnet-20240229-v1:0"
  temperature: 0.2
```

### Testing Your Custom Agent

```bash
# Test configuration validity
strandsflow config --validate my_agent.yaml

# Test agent functionality
strandsflow chat --config my_agent.yaml "Hello, what can you help me with?"

# Start server with custom agent
strandsflow server --config my_agent.yaml --port 8001
```

### Best Practices for Custom Agents

1. **Clear Purpose**: Define a specific role and scope for your agent
2. **Detailed System Prompt**: Provide comprehensive instructions and examples
3. **Appropriate Model**: Choose the right model for your use case (Haiku for speed, Sonnet for complexity)
4. **Tool Selection**: Include only relevant tools to reduce confusion
5. **Temperature Tuning**: Lower for factual tasks, higher for creative tasks
6. **Memory Management**: Set appropriate conversation limits
7. **Testing**: Thoroughly test with various inputs and edge cases

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  StrandsFlow Platform                      │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   REST API  │  │     CLI     │  │   Python Library   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 Strands Agents SDK                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Agents    │  │   Models    │  │       Tools         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                External Services                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ AWS Bedrock │  │ MCP Servers │  │   Built-in Tools    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Development Status

### ✅ Sprint 1: Core Foundation (Complete)
- [x] Project structure and configuration
- [x] Strands SDK integration
- [x] AWS Bedrock model provider
- [x] Built-in tools (calculator, files, python, shell, time)
- [x] Basic REST API with FastAPI
- [x] CLI interface
- [x] Basic testing framework

### ✅ Sprint 2: Enhanced Features (Complete)
- [x] WebSocket streaming support for real-time conversations
- [x] Metrics endpoint for monitoring and observability
- [x] Enhanced configuration with environment profiles
- [x] Advanced MCP server discovery and management
- [x] Connection manager for WebSocket sessions
- [x] Health check endpoints
- [x] Production-ready logging and error handling

### 🔮 Sprint 3: Production Features (Planned)
- [ ] Authentication and authorization
- [ ] Database persistence
- [ ] Advanced monitoring and observability
- [ ] Deployment templates (Docker, Kubernetes)
- [ ] **Multi-agent orchestration and communication**
- [ ] Agent marketplace and templates

### 🤖 Multi-Agent Communication (Future Feature)

**Current Status**: Multi-agent communication is not yet implemented but is planned for Sprint 3.

#### Potential Implementation Approaches:

**1. Message Broker Pattern**
```python
# Future implementation concept
class AgentOrchestrator:
    def __init__(self):
        self.agents = {}
        self.message_broker = MessageBroker()
    
    async def register_agent(self, agent_id: str, agent: StrandsFlowAgent):
        self.agents[agent_id] = agent
        await self.message_broker.subscribe(agent_id, agent.handle_message)
    
    async def send_message(self, from_agent: str, to_agent: str, message: str):
        await self.message_broker.publish(to_agent, {
            "from": from_agent,
            "content": message,
            "timestamp": datetime.now()
        })
```

**2. Shared Context Pattern**
```python
# Agents sharing context through MCP servers
mcp:
  servers:
    shared_context:
      command: ["python", "shared_context_server.py"]
      transport: "stdio"
      config:
        context_store: "redis://localhost:6379"
```

**3. Agent Coordination API**
```python
# Future REST endpoints for agent communication
/api/v1/orchestration/agents/{agent_id}/send:
  POST: # Send message to another agent

/api/v1/orchestration/conversations:
  POST: # Start multi-agent conversation
  GET:  # List active multi-agent conversations

/api/v1/orchestration/workflows:
  POST: # Define agent workflow
  GET:  # List workflows
```

#### Use Cases for Multi-Agent Communication:
- **Code Review Workflow**: Reviewer agent → Developer agent → QA agent
- **Customer Support**: Triage agent → Specialist agent → Follow-up agent
- **Data Analysis Pipeline**: Collector agent → Analyzer agent → Reporter agent
- **Content Creation**: Research agent → Writer agent → Editor agent

#### Current Workarounds:
1. **External Coordination**: Use external services to coordinate between agents
2. **Shared MCP Servers**: Agents can communicate through shared tools
3. **Database Integration**: Store intermediate results for other agents to process
4. **WebSocket Broadcasting**: Broadcast messages to multiple agent sessions

#### Example: Multi-Agent Workflow with Current System

```python
# Simple multi-agent coordinator using current StrandsFlow
import asyncio
from strandsflow.core.agent import StrandsFlowAgent
from strandsflow.core.config import StrandsFlowConfig

class SimpleAgentCoordinator:
    def __init__(self):
        self.agents = {}
        self.shared_context = {}
    
    async def add_agent(self, name: str, config_path: str):
        """Add an agent to the coordinator."""
        config = StrandsFlowConfig.from_file(config_path)
        agent = StrandsFlowAgent(config=config)
        await agent.initialize()
        self.agents[name] = agent
    
    async def sequential_workflow(self, task: str, agent_chain: list):
        """Execute a task through a chain of agents."""
        result = task
        
        for agent_name in agent_chain:
            if agent_name in self.agents:
                print(f"Passing to {agent_name}: {result}")
                result = await self.agents[agent_name].chat(result)
                
                # Store intermediate results
                self.shared_context[f"{agent_name}_output"] = result
        
        return result
    
    async def parallel_analysis(self, task: str, agent_names: list):
        """Run task through multiple agents in parallel."""
        tasks = [
            self.agents[name].chat(task) 
            for name in agent_names 
            if name in self.agents
        ]
        
        results = await asyncio.gather(*tasks)
        return dict(zip(agent_names, results))

# Usage example
async def multi_agent_example():
    coordinator = SimpleAgentCoordinator()
    
    # Add specialized agents
    await coordinator.add_agent("researcher", "research_agent.yaml")
    await coordinator.add_agent("writer", "writer_agent.yaml") 
    await coordinator.add_agent("reviewer", "review_agent.yaml")
    
    # Sequential workflow
    final_result = await coordinator.sequential_workflow(
        "Write a technical blog post about AI agents",
        ["researcher", "writer", "reviewer"]
    )
    
    # Parallel analysis
    analysis_results = await coordinator.parallel_analysis(
        "Analyze this code for bugs and performance issues",
        ["security_agent", "performance_agent", "style_agent"]
    )
    
    print("Final result:", final_result)
    print("Analysis results:", analysis_results)

# Run the example
asyncio.run(multi_agent_example())
```

#### Shared MCP Server for Agent Communication

```python
# shared_message_server.py - MCP server for agent communication
import json
from collections import defaultdict
from mcp.server import Server
from mcp.types import Tool

app = Server("shared-messages")
agent_messages = defaultdict(list)

@app.tool("send_message")
async def send_message(to_agent: str, from_agent: str, message: str) -> str:
    """Send a message to another agent."""
    agent_messages[to_agent].append({
        "from": from_agent,
        "message": message,
        "timestamp": datetime.now().isoformat()
    })
    return f"Message sent to {to_agent}"

@app.tool("get_messages")
async def get_messages(agent_id: str) -> str:
    """Get messages for an agent."""
    messages = agent_messages.get(agent_id, [])
    agent_messages[agent_id] = []  # Clear after reading
    return json.dumps(messages)

if __name__ == "__main__":
    app.run()
```

```yaml
# Agent configuration with shared communication server
mcp:
  servers:
    shared_messages:
      command: ["python", "shared_message_server.py"]
      transport: "stdio"
```

**Note**: These are workarounds with the current system. Native multi-agent communication will be implemented in Sprint 3 with proper orchestration, state synchronization, and built-in coordination patterns.

## 🧪 Testing

```bash
# Run basic tests
strandsflow test

# Test direct Strands SDK integration
python test_basic_strands.py

# Run integration tests
python test_integration.py

# Check configuration
strandsflow config --show

# Test WebSocket streaming
# Open websocket_test.html in browser after starting server
strandsflow server
```

## 📖 Available Tools

StrandsFlow includes these built-in tools from `strands-agents-tools`:

- **calculator**: Mathematical operations and calculations
- **current_time**: Get current date and time information
- **file_read**: Read and parse files from the file system
- **file_write**: Create and modify files
- **python_repl**: Execute Python code in a REPL environment
- **shell**: Execute shell commands and scripts

## 🌐 API Endpoints

### Core Endpoints
- `GET /health` - Health check
- `GET /metrics` - Application metrics and monitoring data
- `POST /api/v1/agents` - Create new agent
- `GET /api/v1/agents` - List all agents
- `GET /api/v1/agents/{agent_id}` - Get agent details
- `DELETE /api/v1/agents/{agent_id}` - Delete agent
- `POST /api/v1/chat` - Chat with agent
- `GET /api/v1/sessions` - List sessions
- `DELETE /api/v1/sessions/{session_id}` - Delete session

### Real-time Endpoints
- `WebSocket /ws/chat` - Real-time streaming chat with agents

### Example WebSocket Usage

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');

ws.onopen = function(event) {
    // Send message to agent
    ws.send(JSON.stringify({
        message: "Hello, what can you help me with?",
        agent_id: "default"
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Agent response:', data.message);
};
```

Full API documentation: http://localhost:8000/docs

## 🔧 Configuration

StrandsFlow can be configured via environment variables or configuration files:

### Environment Variables

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-west-2

# StrandsFlow Configuration
STRANDSFLOW_CONFIG=path/to/config.yaml
STRANDSFLOW_API_HOST=0.0.0.0
STRANDSFLOW_API_PORT=8000
STRANDSFLOW_LOG_LEVEL=INFO
STRANDSFLOW_ENVIRONMENT=production
STRANDSFLOW_ENABLE_METRICS=true
STRANDSFLOW_DEBUG=false
```

### Configuration File Example

```yaml
agent:
  name: "StrandsFlow Agent"
  description: "Production AI agent"
  system_prompt: "You are a helpful AI assistant."
  enable_memory: true
  max_conversation_turns: 50

bedrock:
  model_id: "anthropic.claude-3-haiku-20240307-v1:0"
  region_name: "us-west-2"
  temperature: 0.7
  max_tokens: 4096
  streaming: true

api:
  host: "0.0.0.0"
  port: 8000
  workers: 1
  reload: false
  cors_origins: ["*"]

environment:
  name: "production"
  debug: false
  log_level: "INFO"
  enable_metrics: true
  max_concurrent_connections: 100
  rate_limit_requests: 60

mcp:
  auto_discover: true
  connection_timeout: 30
  default_transport: "stdio"
  discovery_paths:
    - "~/.mcp/servers"
    - "/usr/local/mcp/servers"
  servers: {}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🔗 Links

- [Strands Agents SDK Documentation](https://strandsagents.com)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

**StrandsFlow** - AI Agent Platform built on Strands SDK ⚡

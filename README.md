# StrandsFlow

🚀 **AI Agent Platform built on Strands Agents SDK**

StrandsFlow is a production-ready AI agent platform that extends the [Strands Agents SDK](https://strandsagents.com) with AWS Bedrock integration and Model Context Protocol (MCP) support.

## ✨ Features

- **🏗️ Built on Strands SDK**: Production-ready agent framework with official Strands Agents SDK
- **☁️ AWS Bedrock Integration**: Native support for Claude 4 Sonnet and other Bedrock models
- **🔧 Rich Tool Ecosystem**: File operations, Python execution, shell commands, calculations via strands-agents-tools
- **🌐 REST API**: FastAPI-based endpoints for agent interactions with async/streaming support
- **⚡ Real-time Streaming**: Async responses and streaming conversations
- **🔌 MCP Protocol**: Extensible tool ecosystem via Model Context Protocol
- **📊 Observability**: Built-in structured logging and metrics
- **🖥️ CLI Interface**: Rich command-line interface with Typer and Rich
- **⚙️ Configuration Management**: Flexible config with environment variables, files (JSON/YAML)

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd strands_agent

# Create virtual environment (requires Python 3.11+)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
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

**Note**: Ensure you have access to Claude 4 Sonnet in Amazon Bedrock console.

### CLI Usage

```bash
# Add src to Python path
export PYTHONPATH=src

# Initialize configuration
python -m strandsflow.cli init

# Start interactive chat
python -m strandsflow.cli chat

# View configuration
python -m strandsflow.cli config --show

# Start API server
python -m strandsflow.cli server

# Check version
python -m strandsflow.cli version
```
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install strands-agents strands-agents-tools fastapi uvicorn pydantic structlog httpx aiofiles typer rich websockets
```

### AWS Configuration

StrandsFlow uses AWS Bedrock for LLM capabilities. Configure your AWS credentials:

```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-west-2
```

**Note**: You need to enable Claude 4 Sonnet model access in Amazon Bedrock console.

### Basic Usage

#### CLI Interface

```bash
# Test the installation
PYTHONPATH=src python -m strandsflow.cli test

# Get platform information
PYTHONPATH=src python -m strandsflow.cli info

# Chat with an agent
PYTHONPATH=src python -m strandsflow.cli chat "What's 15 * 23?"

# Start the API server
PYTHONPATH=src python -m strandsflow.cli server
```

#### Python API

```python
from strands import Agent
from strands.models import BedrockModel
from strands_tools import calculator, current_time, file_read

# Create agent with Bedrock
model = BedrockModel(
    model_id="anthropic.claude-sonnet-4-20250514-v1:0",
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
PYTHONPATH=src python -m strandsflow.cli server
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

### ✅ Sprint 1: Core Foundation (Current)
- [x] Project structure and configuration
- [x] Strands SDK integration
- [x] AWS Bedrock model provider
- [x] Built-in tools (calculator, files, python, shell, time)
- [x] Basic REST API with FastAPI
- [x] CLI interface
- [x] Basic testing framework

### 🔄 Sprint 2: MCP Integration (Next)
- [ ] MCP client implementation
- [ ] Multiple MCP server support (stdio, SSE, HTTP)
- [ ] Tool discovery and registration
- [ ] Advanced configuration management

### 🔮 Sprint 3: Production Features
- [ ] Authentication and authorization
- [ ] Database persistence
- [ ] Advanced monitoring and observability
- [ ] Deployment templates (Docker, Kubernetes)

## 🧪 Testing

```bash
# Run basic tests
PYTHONPATH=src python -m strandsflow.cli test

# Test direct Strands SDK integration
python test_basic_strands.py

# Check configuration
PYTHONPATH=src python -m strandsflow.cli config
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

- `GET /health` - Health check
- `POST /api/v1/agents` - Create new agent
- `GET /api/v1/agents` - List all agents
- `GET /api/v1/agents/{agent_id}` - Get agent details
- `DELETE /api/v1/agents/{agent_id}` - Delete agent
- `POST /api/v1/chat` - Chat with agent
- `GET /api/v1/sessions` - List sessions
- `DELETE /api/v1/sessions/{session_id}` - Delete session

Full API documentation: http://localhost:8000/docs

## 🔧 Configuration

StrandsFlow can be configured via environment variables:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-west-2

# StrandsFlow Configuration
STRANDSFLOW_API_HOST=0.0.0.0
STRANDSFLOW_API_PORT=8000
STRANDSFLOW_LOG_LEVEL=INFO
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

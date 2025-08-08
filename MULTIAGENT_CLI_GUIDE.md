# StrandsFlow Multi-Agent CLI - Complete User Guide

## Overview

StrandsFlow now provides full CLI support for creating and managing multiple agents that can communicate with each other using Agent-to-Agent (A2A) protocols. This guide shows you how to create, configure, and use multiple agents via the command line.

## Quick Start

### 1. Create Multiple Agents

```bash
# Create 2 agents (assistant and researcher)
strandsflow multiagent create --agents assistant,researcher --workspace my_agents --base-port 8000

# Create 3 agents with custom specializations
strandsflow multiagent create --agents assistant,researcher,writer --workspace team_agents --base-port 8010
```

### 2. Agent-to-Agent Chat

```bash
# Interactive chat between two specific agents
strandsflow multiagent chat --workspace my_agents --agent1 assistant --agent2 researcher

# Let CLI guide you through agent selection
strandsflow multiagent chat --workspace my_agents
```

### 3. Task Orchestration

```bash
# Route a task across multiple agents
strandsflow multiagent orchestrate "Research AI trends and write a report" --workspace my_agents

# Use specific agents only
strandsflow multiagent orchestrate "Code review this Python script" --workspace my_agents --agents coder,reviewer
```

## Detailed Commands

### Creating Multi-Agent Workspaces

The `multiagent create` command sets up a complete multi-agent environment:

```bash
strandsflow multiagent create [OPTIONS]

Options:
  --agents TEXT        Comma-separated list of agent types (default: assistant,researcher)
  --workspace TEXT     Directory for agent configurations (default: multiagent_workspace)  
  --base-port INTEGER  Starting port number (each agent gets port+1) (default: 8000)
  --model TEXT         Bedrock model ID for all agents (default: claude-3-haiku)
```

**Available Agent Types:**
- `assistant` - General-purpose coordinator and user interface
- `researcher` - Information gathering and analysis specialist  
- `analyst` - Data analysis and business intelligence expert
- `writer` - Content creation and writing specialist
- `coder` - Software development and code review expert

**What Gets Created:**
- Individual agent configuration files (`{agent}_config.yaml`)
- Orchestrator configuration (`orchestrator_config.yaml`)
- Startup script (`start_agents.py`) 
- Interactive chat script (`agent_chat.py`)
- A2A communication test (`test_a2a_communication.py`)

### Agent-to-Agent Communication

#### Interactive Chat Mode

```bash
strandsflow multiagent chat --workspace my_agents --agent1 assistant --agent2 researcher
```

This starts an interactive chat session where:
- You can send messages to either agent
- Agents alternate responses
- Use format `agent_name: message` to specify which agent
- Type `quit` to exit

#### Programmatic Communication

```bash
# Single message to specific agent
strandsflow chat --config my_agents/assistant_config.yaml --message "Hello, can you help me?"

# Start interactive session with one agent
strandsflow chat --config my_agents/researcher_config.yaml
```

### Task Orchestration

Route complex tasks across multiple specialized agents:

```bash
strandsflow multiagent orchestrate "Create a business plan for a tech startup" --workspace my_agents

# Results saved to: my_agents/orchestration_results_{timestamp}.json
```

The orchestrator:
1. Analyzes the task requirements
2. Routes to appropriate specialists
3. Collects and consolidates responses
4. Saves results with timestamps

## Configuration Files

Each agent gets a dedicated configuration file with:

```yaml
# Example: assistant_config.yaml
agent:
  name: "Assistant Agent"
  description: "General-purpose AI assistant for task coordination"
  system_prompt: "You are a helpful AI assistant that specializes in..."

api:
  host: "127.0.0.1"
  port: 8000
  
a2a:  # Agent-to-Agent configuration
  agent_id: "assistant_agent"
  server_port: 8100
  peers:
    - agent_id: "researcher_agent"
      endpoint: "http://localhost:8101"
      
bedrock:
  model_id: "anthropic.claude-3-haiku-20240307-v1:0"
  temperature: 0.7
  max_tokens: 4096
```

## Running Agents

### Start All Agents

```bash
cd my_agents
python start_agents.py
```

This starts all agents in the background on their configured ports.

### Start Individual Agents

```bash
# Start specific agent server
strandsflow server --config my_agents/assistant_config.yaml

# Override port
strandsflow server --config my_agents/researcher_config.yaml --port 8005
```

### Verify Agents are Running

```bash
# Health check via curl
curl http://localhost:8000/health
curl http://localhost:8001/health

# Or use the test script
cd my_agents
python test_a2a_communication.py
```

## Communication Patterns

### 1. Direct A2A (Peer-to-Peer)
```
User → Assistant Agent ↔ Researcher Agent
```
Agents communicate directly with each other.

### 2. Orchestrated Workflow  
```
User → Orchestrator → [Assistant, Researcher, Writer] → Consolidated Response
```
Central orchestrator routes tasks to appropriate specialists.

### 3. Sequential Pipeline
```
User → Assistant → Researcher → Writer → Final Output
```
Tasks flow through agents in sequence.

### 4. Parallel Processing
```
User → [Assistant, Researcher, Writer] (simultaneously) → Combined Results
```
Multiple agents work on the same task in parallel.

## API Integration

When agents are running, you can use the REST API:

### Chat with Specific Agent
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello!", "session_id": "my-session"}'
```

### Orchestrate Tasks
```bash
curl -X POST "http://localhost:8000/api/v1/multiagent/orchestrate" \
  -H "Content-Type: application/json" \
  -d '{"task": "Research and write about AI", "workflow_type": "sequential"}'
```

### List Available Agents
```bash
curl "http://localhost:8000/api/v1/multiagent/specialists"
```

## Examples

### Example 1: Content Creation Team
```bash
# Create content team
strandsflow multiagent create --agents researcher,writer,analyst --workspace content_team

# Research and write article
strandsflow multiagent orchestrate "Research renewable energy trends and write a blog post" --workspace content_team
```

### Example 2: Development Team
```bash
# Create dev team  
strandsflow multiagent create --agents assistant,coder,reviewer --workspace dev_team

# Code review workflow
strandsflow multiagent orchestrate "Review this Python script for security issues" --workspace dev_team
```

### Example 3: Research Team
```bash
# Create research team
strandsflow multiagent create --agents assistant,researcher,analyst --workspace research_team

# Collaborative research
strandsflow multiagent chat --workspace research_team --agent1 researcher --agent2 analyst
```

## Troubleshooting

### Agents Not Starting
```bash
# Check configuration
strandsflow config --show --config my_agents/assistant_config.yaml

# Check ports aren't in use
lsof -i :8000
```

### Import Errors
```bash
# Set Python path
export PYTHONPATH="/path/to/strands_agent/src:$PYTHONPATH"

# Or install in development mode
pip install -e .
```

### AWS Credentials
```bash
# Configure AWS credentials for actual agent communication
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-west-2
```

## Advanced Usage

### Custom Agent Types
You can add custom agent specializations by modifying the agent templates in the CLI code or using the `custom` type:

```bash
strandsflow multiagent create --agents custom,custom --workspace custom_agents
# Then manually edit the configuration files
```

### Scaling Agents
```bash
# Use different port ranges for multiple workspaces
strandsflow multiagent create --agents team1_assistant,team1_researcher --base-port 8000
strandsflow multiagent create --agents team2_assistant,team2_researcher --base-port 8010
```

### Integration with External Services
Agents can be configured to use different models, regions, or MCP servers by editing their individual configuration files.

## Summary

The StrandsFlow CLI now provides complete support for:

✅ **Multi-agent creation** - Set up teams of specialized agents  
✅ **A2A communication** - Direct agent-to-agent interaction  
✅ **Interactive chat** - Chat between any two agents via CLI  
✅ **Task orchestration** - Route complex tasks across agent teams  
✅ **Flexible configuration** - Customize each agent's behavior  
✅ **Production deployment** - API servers for programmatic access

This enables you to create sophisticated multi-agent workflows entirely from the command line, with agents that can coordinate, collaborate, and communicate with each other to solve complex tasks.

---

*For more information, see the project documentation and API reference at http://localhost:8000/docs when your agents are running.*

# 🤖 StrandsFlow Multi-Agent Setup Guide

This guide shows you how to set up and use StrandsFlow's multi-agent communication system, built on the Strands Agents SDK with A2A (Agent-to-Agent) protocol.

## 🚀 Quick Start

### 1. Basic Multi-Agent Setup

```python
import asyncio
from strandsflow.multiagent import (
    create_predefined_pool, Orchestrator, A2AServerManager, WorkflowType
)
from strandsflow.core.config import StrandsFlowConfig

async def basic_multiagent_example():
    # Create configuration
    config = StrandsFlowConfig()
    
    # Create specialist pool with predefined agents
    pool = await create_predefined_pool(config)
    await pool.initialize_all()
    
    # Available specialists:
    # - Code Expert: Programming, debugging, architecture
    # - Data Analyst: Data analysis, ML, statistics  
    # - Content Writer: Writing, editing, SEO
    # - Research Assistant: Research, analysis, fact-checking
    # - Customer Support: Customer service, problem-solving
    
    # Set up A2A communication
    a2a_manager = A2AServerManager()
    orchestrator = Orchestrator(a2a_manager=a2a_manager)
    
    # Add specialists to orchestrator
    for name, agent in pool.specialists.items():
        config_obj = pool.configs[name]
        orchestrator.add_specialist(
            name, agent, config_obj.role, config_obj.capabilities
        )
    
    # Create orchestrator agent
    orchestrator.create_orchestrator_agent()
    
    # Use the orchestrator for intelligent task routing
    result = await orchestrator.execute_workflow(
        task="Write a Python function to analyze sales data",
        workflow_type=WorkflowType.CONDITIONAL
    )
    
    print(f"Task routed to: {result['routing_decision']}")
    
    # Cleanup
    await pool.shutdown_all()

# Run the example
asyncio.run(basic_multiagent_example())
```

### 2. Custom Specialist Creation

```python
from strandsflow.core.agent import StrandsFlowAgent
from strandsflow.core.config import StrandsFlowConfig
from strandsflow.multiagent import SpecialistPool

async def create_custom_specialists():
    config = StrandsFlowConfig()
    pool = SpecialistPool()
    
    # Create custom specialist configurations
    custom_specialists = {
        "Security Expert": {
            "role": "Senior Security Engineer",
            "capabilities": ["security_audit", "penetration_testing", "compliance"],
            "system_prompt": """You are a cybersecurity expert with deep knowledge of:
            - Security vulnerabilities and threat modeling
            - Penetration testing and security auditing
            - Compliance frameworks (SOC2, GDPR, HIPAA)
            - Secure coding practices and architecture
            
            Always prioritize security best practices and provide actionable recommendations.""",
            "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
            "temperature": 0.3
        },
        
        "DevOps Engineer": {
            "role": "Senior DevOps Engineer", 
            "capabilities": ["ci_cd", "infrastructure", "monitoring", "automation"],
            "system_prompt": """You are a DevOps expert specializing in:
            - CI/CD pipeline design and optimization
            - Infrastructure as Code (Terraform, CloudFormation)
            - Container orchestration (Docker, Kubernetes)
            - Monitoring and observability
            - Cloud platforms (AWS, Azure, GCP)
            
            Focus on scalable, reliable, and automated solutions.""",
            "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
            "temperature": 0.4
        }
    }
    
    # Add custom specialists to pool
    for name, spec in custom_specialists.items():
        # Create custom config
        custom_config = StrandsFlowConfig()
        custom_config.agent.name = name
        custom_config.agent.system_prompt = spec["system_prompt"]
        custom_config.bedrock.model_id = spec["model_id"]
        custom_config.bedrock.temperature = spec["temperature"]
        
        # Create and add specialist
        agent = StrandsFlowAgent(config=custom_config)
        await pool.add_specialist(
            name=name,
            agent=agent,
            role=spec["role"],
            capabilities=spec["capabilities"],
            config=custom_config
        )
    
    # Initialize all specialists
    await pool.initialize_all()
    
    # List available specialists
    specialists = pool.list_specialists()
    print("Available Specialists:")
    for name, info in specialists.items():
        print(f"  • {name}: {info['role']}")
        print(f"    Capabilities: {', '.join(info['capabilities'])}")
    
    return pool

# Usage
pool = asyncio.run(create_custom_specialists())
```

### 3. A2A Server Setup

```python
from strandsflow.multiagent import A2AServerManager
from strandsflow.core.agent import StrandsFlowAgent

async def setup_a2a_network():
    # Create A2A server manager
    a2a_manager = A2AServerManager()
    
    # Create and register agents as A2A servers
    agents = {}
    
    # Math specialist
    math_config = StrandsFlowConfig()
    math_config.agent.name = "Math Specialist"
    math_config.agent.system_prompt = "You are a mathematics expert. Solve problems step by step."
    
    math_agent = StrandsFlowAgent(config=math_config)
    await math_agent.initialize()
    
    # Register as A2A server (automatically starts on available port)
    math_server = await a2a_manager.add_agent(math_agent, "math_specialist")
    print(f"Math Specialist A2A endpoint: {math_server.get_endpoint()}")
    
    # Code specialist  
    code_config = StrandsFlowConfig()
    code_config.agent.name = "Code Specialist"
    code_config.agent.system_prompt = "You are a programming expert. Write clean, efficient code."
    
    code_agent = StrandsFlowAgent(config=code_config)
    await code_agent.initialize()
    
    code_server = await a2a_manager.add_agent(code_agent, "code_specialist")
    print(f"Code Specialist A2A endpoint: {code_server.get_endpoint()}")
    
    # List all A2A servers
    servers = a2a_manager.list_agents()
    print("\\nA2A Network:")
    for name, card in servers.items():
        print(f"  • {card['name']}: {card['endpoint']}")
        print(f"    Capabilities: {', '.join(card['capabilities'])}")
    
    return a2a_manager

# Setup A2A network
a2a_network = asyncio.run(setup_a2a_network())
```

### 4. Multi-Agent Workflows

```python
from strandsflow.multiagent import WorkflowManager, WorkflowType

async def workflow_examples():
    # Setup (assuming you have pool and orchestrator from previous examples)
    config = StrandsFlowConfig()
    pool = await create_predefined_pool(config)
    await pool.initialize_all()
    
    a2a_manager = A2AServerManager()
    orchestrator = Orchestrator(a2a_manager=a2a_manager)
    
    # Add specialists to orchestrator
    for name, agent in pool.specialists.items():
        config_obj = pool.configs[name]
        orchestrator.add_specialist(name, agent, config_obj.role, config_obj.capabilities)
    
    workflow_manager = WorkflowManager(orchestrator, pool)
    
    # Example 1: Sequential workflow (content creation)
    print("🔄 Sequential Workflow: Content Creation")
    
    content_inputs = {
        "topic": "AI in Healthcare",
        "audience": "medical professionals"
    }
    
    execution_id = await workflow_manager.execute_workflow(
        workflow_name="content_creation",
        inputs=content_inputs
    )
    
    # Monitor execution
    for i in range(30):
        await asyncio.sleep(1)
        execution = workflow_manager.get_execution_status(execution_id)
        
        if execution and execution.status.value in ["completed", "failed"]:
            print(f"Workflow {execution.status.value}")
            break
    
    # Example 2: Parallel workflow (multiple perspectives)
    print("\\n⚡ Parallel Workflow: Multiple Perspectives")
    
    task = "Analyze the impact of remote work on productivity"
    agents = ["Research Assistant", "Data Analyst", "Content Writer"]
    
    result = await orchestrator.execute_workflow(
        task=task,
        workflow_type=WorkflowType.PARALLEL,
        agents=agents
    )
    
    print("Parallel execution results:")
    for agent_result in result.get("results", []):
        agent_name = agent_result.get("agent", "Unknown")
        print(f"  • {agent_name}: [output truncated]")
    
    # Example 3: Conditional routing (intelligent task routing)
    print("\\n🧠 Conditional Workflow: Intelligent Routing")
    
    tasks = [
        "Debug this Python code that's causing memory leaks",
        "Write a blog post about sustainable technology", 
        "Analyze customer churn data and recommend actions",
        "Help a customer who can't access their account"
    ]
    
    for task in tasks:
        result = await orchestrator.execute_workflow(
            task=task,
            workflow_type=WorkflowType.CONDITIONAL
        )
        
        routed_agent = result.get("routing_decision", "Unknown")
        print(f"  Task: {task[:50]}...")
        print(f"  Routed to: {routed_agent}")
    
    await pool.shutdown_all()

# Run workflow examples
asyncio.run(workflow_examples())
```

### 5. API Integration

```python
# Start the StrandsFlow server with multi-agent support
from strandsflow.api.app import app
import uvicorn

# The API automatically includes multi-agent endpoints:
# POST /api/v1/multiagent/orchestrate - Route tasks to specialists
# POST /api/v1/multiagent/workflows/execute - Execute predefined workflows  
# GET /api/v1/multiagent/specialists - List available specialists
# GET /api/v1/multiagent/workflows - List available workflows

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 6. CLI Usage

```bash
# Start the multi-agent server
strandsflow server

# Test multi-agent functionality via API
curl -X POST "http://localhost:8000/api/v1/multiagent/orchestrate" \\
  -H "Content-Type: application/json" \\
  -d '{
    "task": "Create a Python web scraper for e-commerce sites",
    "workflow_type": "conditional"
  }'

# List available specialists
curl "http://localhost:8000/api/v1/multiagent/specialists"

# Execute a predefined workflow
curl -X POST "http://localhost:8000/api/v1/multiagent/workflows/execute" \\
  -H "Content-Type: application/json" \\
  -d '{
    "workflow_name": "software_development",
    "inputs": {
      "project_name": "Task Manager App",
      "requirements": "Web-based task management with user authentication"
    }
  }'
```

## 🔧 Configuration

### Environment Setup

```bash
# AWS Configuration (required for Bedrock)
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-west-2

# StrandsFlow Configuration
export STRANDSFLOW_CONFIG=multiagent_config.yaml
export STRANDSFLOW_ENABLE_MULTIAGENT=true
```

### Configuration File Example

```yaml
# multiagent_config.yaml
agent:
  name: "Multi-Agent Orchestrator"
  description: "Coordinates multiple specialist agents"
  enable_memory: true

bedrock:
  model_id: "anthropic.claude-3-sonnet-20240229-v1:0"
  region_name: "us-west-2"
  temperature: 0.7

multiagent:
  enable_a2a: true
  orchestrator_model: "anthropic.claude-3-sonnet-20240229-v1:0"
  specialist_model: "anthropic.claude-3-haiku-20240307-v1:0"
  max_parallel_agents: 5
  workflow_timeout: 300
  
  # Custom specialists
  specialists:
    - name: "Legal Expert"
      role: "Senior Legal Counsel"
      capabilities: ["contract_review", "compliance", "legal_analysis"]
      model_id: "anthropic.claude-3-sonnet-20240229-v1:0"
      temperature: 0.2
      system_prompt: "You are a legal expert specializing in technology law..."

api:
  host: "0.0.0.0"
  port: 8000
  enable_multiagent_endpoints: true
```

## 🎯 Multi-Agent Patterns

### 1. Orchestrator Pattern
Central coordinator that routes tasks to appropriate specialists based on capabilities and context.

### 2. Pipeline Pattern  
Sequential processing where each agent's output becomes the next agent's input.

### 3. Swarm Pattern
Parallel processing where multiple agents work on the same task independently.

### 4. Hierarchical Pattern
Master-worker hierarchy with specialized teams for different domains.

### 5. Federation Pattern
Cross-platform agent communication using A2A protocol.

## 🚨 Prerequisites

1. **AWS Account**: With Bedrock access and Claude model permissions
2. **Python 3.8+**: With async/await support
3. **Dependencies**: Install with `pip install 'strands-agents[a2a]' 'strands-agents-tools[a2a_client]'`
4. **Configuration**: AWS credentials and StrandsFlow config

## 📚 Available Specialist Types

- **Code Expert**: Programming, debugging, architecture, testing
- **Data Analyst**: Data analysis, ML, statistics, visualization  
- **Content Writer**: Writing, editing, SEO, content strategy
- **Research Assistant**: Research, analysis, fact-checking
- **Customer Support**: Customer service, problem-solving
- **Custom Specialists**: Create your own with specific roles and capabilities

## 🔗 Integration Examples

### With External A2A Agents
```python
# Connect to external A2A agents
from strands_tools.a2a_client import A2AClientToolProvider

provider = A2AClientToolProvider(
    known_agent_urls=["http://external-agent:9000"]
)

orchestrator_agent = Agent(
    tools=provider.tools + local_specialist_tools,
    instructions="Route tasks to appropriate agents, including external ones"
)
```

### With MCP Servers
```python
# Add MCP servers for extended capabilities
mcp_servers = [
    {
        "name": "database_tools",
        "command": ["node", "db-server.js"],
        "transport": "stdio"
    }
]

agent = StrandsFlowAgent(mcp_servers=mcp_servers)
```

This setup gives you a complete multi-agent system with intelligent task routing, parallel processing, and A2A communication capabilities!

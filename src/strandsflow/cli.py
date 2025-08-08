#!/usr/bin/env python3
"""
StrandsFlow CLI

Command-line interface for the StrandsFlow AI agent platform.
Provides tools for agent creation, configuration, and interaction.
"""

import asyncio
import sys
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import print as rprint

from .core.config import StrandsFlowConfig
from .core.agent import StrandsFlowAgent
from .multiagent.orchestrator import Orchestrator
from .multiagent.a2a_server import A2AServer, A2AClient

app = typer.Typer(
    name="strandsflow",
    help="StrandsFlow AI Agent Platform CLI",
    rich_markup_mode="rich"
)

# Add multi-agent subcommand group
multiagent_app = typer.Typer(
    name="multiagent",
    help="Multi-agent management and communication",
    rich_markup_mode="rich"
)
app.add_typer(multiagent_app, name="multiagent")

console = Console()


@app.command()
def init(
    config_path: str = typer.Option(
        "strandsflow.yaml",
        "--config",
        "-c",
        help="Path to configuration file"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing configuration"
    )
):
    """Initialize a new StrandsFlow configuration."""
    
    config_file = Path(config_path)
    
    if config_file.exists() and not force:
        rprint(f"[red]Configuration file already exists: {config_path}[/red]")
        rprint("Use --force to overwrite")
        raise typer.Exit(1)
    
    # Create default configuration
    config = StrandsFlowConfig()
    
    try:
        config.save_to_file(config_path)
        rprint(f"[green]✅ Configuration created: {config_path}[/green]")
        rprint(f"[blue]📝 Agent name: {config.agent.name}[/blue]")
        rprint(f"[blue]🤖 Model: {config.bedrock.model_id}[/blue]")
        rprint(f"[blue]🌍 Region: {config.bedrock.region_name}[/blue]")
    except Exception as e:
        rprint(f"[red]❌ Failed to create configuration: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def chat(
    config_path: str = typer.Option(
        "strandsflow.yaml",
        "--config",
        "-c",
        help="Path to configuration file"
    ),
    message: Optional[str] = typer.Option(
        None,
        "--message",
        "-m",
        help="Single message to send"
    )
):
    """Start an interactive chat session with the agent."""
    
    async def run_chat():
        try:
            # Load configuration
            if Path(config_path).exists():
                config = StrandsFlowConfig.from_file(config_path)
                rprint(f"[green]📁 Loaded config from: {config_path}[/green]")
            else:
                config = StrandsFlowConfig()
                rprint("[yellow]⚠️ Using default configuration[/yellow]")
            
            # Create agent
            agent = StrandsFlowAgent(config=config)
            await agent.initialize()
            
            rprint(f"[blue]🤖 {config.agent.name} is ready![/blue]")
            rprint(f"[dim]Model: {config.bedrock.model_id}[/dim]")
            
            if message:
                # Single message mode
                rprint(f"\n[bold]User:[/bold] {message}")
                response = await agent.chat(message)
                rprint(f"[bold]{config.agent.name}:[/bold] {response}")
            else:
                # Interactive mode
                rprint("\n[green]💬 Interactive chat mode (type 'quit' to exit)[/green]")
                
                while True:
                    try:
                        user_input = Prompt.ask("\n[bold blue]You[/bold blue]")
                        
                        if user_input.lower() in ['quit', 'exit', 'q']:
                            break
                        
                        if not user_input.strip():
                            continue
                        
                        # Get response from agent
                        response = await agent.chat(user_input)
                        rprint(f"[bold green]{config.agent.name}[/bold green]: {response}")
                        
                    except KeyboardInterrupt:
                        break
                    except EOFError:
                        break
            
            # Cleanup
            await agent.shutdown()
            rprint("\n[dim]👋 Goodbye![/dim]")
            
        except Exception as e:
            rprint(f"[red]❌ Error: {e}[/red]")
            raise typer.Exit(1)
    
    asyncio.run(run_chat())


@app.command()
def config(
    config_path: str = typer.Option(
        "strandsflow.yaml",
        "--config",
        "-c",
        help="Path to configuration file"
    ),
    show: bool = typer.Option(
        False,
        "--show",
        "-s",
        help="Show current configuration"
    )
):
    """Manage StrandsFlow configuration."""
    
    if show:
        try:
            if Path(config_path).exists():
                config = StrandsFlowConfig.from_file(config_path)
                rprint(f"[green]📁 Configuration from: {config_path}[/green]")
            else:
                config = StrandsFlowConfig()
                rprint("[yellow]⚠️ Default configuration (no file found)[/yellow]")
            
            # Display configuration in a table
            table = Table(title="StrandsFlow Configuration")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="magenta")
            
            table.add_row("Agent Name", config.agent.name)
            table.add_row("Agent Description", config.agent.description[:50] + "...")
            table.add_row("Model ID", config.bedrock.model_id)
            table.add_row("Region", config.bedrock.region_name)
            table.add_row("Temperature", str(config.bedrock.temperature))
            table.add_row("Max Tokens", str(config.bedrock.max_tokens))
            table.add_row("Streaming", str(config.bedrock.streaming))
            table.add_row("API Host", config.api.host)
            table.add_row("API Port", str(config.api.port))
            
            console.print(table)
            
        except Exception as e:
            rprint(f"[red]❌ Error reading configuration: {e}[/red]")
            raise typer.Exit(1)
    else:
        rprint("[yellow]Use --show to display configuration[/yellow]")


@app.command()
def server(
    config_path: str = typer.Option(
        "strandsflow.yaml",
        "--config",
        "-c",
        help="Path to configuration file"
    ),
    host: Optional[str] = typer.Option(
        None,
        "--host",
        "-h",
        help="Override API host"
    ),
    port: Optional[int] = typer.Option(
        None,
        "--port",
        "-p",
        help="Override API port"
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        "-r",
        help="Enable auto-reload for development"
    )
):
    """Start the StrandsFlow API server."""
    
    try:
        # Load configuration
        if Path(config_path).exists():
            config = StrandsFlowConfig.from_file(config_path)
            rprint(f"[green]📁 Loaded config from: {config_path}[/green]")
        else:
            config = StrandsFlowConfig()
            rprint("[yellow]⚠️ Using default configuration[/yellow]")
        
        # Override with CLI arguments
        if host:
            config.api.host = host
        if port:
            config.api.port = port
        if reload:
            config.api.reload = reload
        
        rprint(f"[blue]🚀 Starting StrandsFlow API server[/blue]")
        rprint(f"[dim]Host: {config.api.host}[/dim]")
        rprint(f"[dim]Port: {config.api.port}[/dim]")
        rprint(f"[dim]Reload: {config.api.reload}[/dim]")
        
        # Import and start the API server
        import uvicorn
        uvicorn.run(
            "strandsflow.api.app:app",
            host=config.api.host,
            port=config.api.port,
            reload=config.api.reload,
            log_level="info"
        )
        
    except Exception as e:
        rprint(f"[red]❌ Error starting server: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def version():
    """Show StrandsFlow version information."""
    from . import __version__
    
    table = Table(title="StrandsFlow Version Information")
    table.add_column("Component", style="cyan")
    table.add_column("Version", style="magenta")
    
    table.add_row("StrandsFlow", __version__)
    
    try:
        import strands
        table.add_row("Strands SDK", strands.__version__)
    except:
        table.add_row("Strands SDK", "Unknown")
    
    try:
        import boto3
        table.add_row("boto3", boto3.__version__)
    except:
        table.add_row("boto3", "Not installed")
    
    console.print(table)


@app.command()
def create(
    agent_type: str = typer.Argument(..., help="Type of agent to create (data-analysis, code-review, custom)"),
    name: str = typer.Option("My Custom Agent", "--name", "-n", help="Agent name"),
    config_file: str = typer.Option("custom_agent_config.yaml", "--config", "-c", help="Config file path"),
    model: str = typer.Option("anthropic.claude-3-haiku-20240307-v1:0", "--model", "-m", help="Bedrock model ID"),
    port: int = typer.Option(8001, "--port", "-p", help="API server port"),
):
    """Create a new custom agent configuration."""
    
    try:
        # Predefined agent templates
        agent_templates = {
            "data-analysis": {
                "name": f"{name} - Data Analysis Expert",
                "description": "Specialized AI agent for data analysis, statistics, and business intelligence",
                "system_prompt": """You are a data analysis expert with deep knowledge of:
- Statistical analysis and hypothesis testing
- Data visualization and reporting
- Business intelligence and KPI tracking
- Machine learning model interpretation
- Database querying and data processing

Always provide step-by-step analysis, show your reasoning, and suggest actionable insights.""",
                "max_tokens": 8192,
                "temperature": 0.3
            },
            "code-review": {
                "name": f"{name} - Code Review Specialist",
                "description": "Expert code reviewer focusing on quality, security, and best practices",
                "system_prompt": """You are a senior software engineer and code review expert specializing in:
- Code quality assessment and improvement
- Security vulnerability detection
- Performance optimization
- Best practices and design patterns
- Documentation and maintainability

Provide detailed, constructive feedback with specific examples and suggestions.""",
                "max_tokens": 6144,
                "temperature": 0.2
            },
            "customer-support": {
                "name": f"{name} - Customer Support Assistant",
                "description": "Friendly and helpful customer support agent",
                "system_prompt": """You are a helpful and empathetic customer support representative with expertise in:
- Troubleshooting technical issues
- Product knowledge and feature explanations
- Order management and billing inquiries
- Escalation procedures
- Customer satisfaction

Always be polite, patient, and solution-oriented. Ask clarifying questions when needed.""",
                "max_tokens": 4096,
                "temperature": 0.7
            },
            "creative-writing": {
                "name": f"{name} - Creative Writing Assistant",
                "description": "Creative writing companion for stories, content, and ideas",
                "system_prompt": """You are a creative writing expert and storytelling companion skilled in:
- Creative fiction and narrative development
- Content creation and copywriting
- Character development and dialogue
- Plot structure and pacing
- Style adaptation and voice consistency

Help users develop compelling narratives and engaging content.""",
                "max_tokens": 6144,
                "temperature": 0.8
            },
            "custom": {
                "name": name,
                "description": "Custom AI agent with flexible configuration",
                "system_prompt": "You are a helpful AI assistant. Customize this prompt for your specific use case.",
                "max_tokens": 4096,
                "temperature": 0.7
            }
        }
        
        if agent_type not in agent_templates:
            rprint(f"[red]Error: Unknown agent type '{agent_type}'[/red]")
            rprint(f"[yellow]Available types: {', '.join(agent_templates.keys())}[/yellow]")
            raise typer.Exit(1)
        
        template = agent_templates[agent_type]
        
        # Create configuration
        config_data = {
            "agent": {
                "name": template["name"],
                "description": template["description"],
                "enable_memory": True,
                "max_conversation_turns": 50,
                "system_prompt": template["system_prompt"]
            },
            "api": {
                "cors_origins": ["*"],
                "host": "127.0.0.1",
                "port": port,
                "reload": False,
                "workers": 1
            },
            "bedrock": {
                "cache_prompt": None,
                "cache_tools": None,
                "guardrail_id": None,
                "guardrail_trace": "enabled",
                "guardrail_version": None,
                "max_tokens": template["max_tokens"],
                "model_id": model,
                "region_name": "us-west-2",
                "stop_sequences": None,
                "streaming": True,
                "temperature": template["temperature"],
                "top_p": None
            },
            "mcp": {
                "auto_discover": True,
                "connection_timeout": 30,
                "default_transport": "stdio",
                "discovery_paths": [
                    "~/.mcp/servers",
                    "/usr/local/mcp/servers"
                ],
                "servers": {}
            },
            "environment": {
                "name": "development",
                "debug": True,
                "log_level": "INFO",
                "enable_metrics": True,
                "rate_limit_requests": 60,
                "max_concurrent_connections": 100
            }
        }
        
        # Write configuration file
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)
        
        rprint(f"[green]✅ Created custom agent configuration: {config_file}[/green]")
        rprint(f"[blue]Agent Type: {agent_type}[/blue]")
        rprint(f"[blue]Agent Name: {template['name']}[/blue]")
        rprint(f"[blue]Port: {port}[/blue]")
        rprint(f"[blue]Model: {model}[/blue]")
        
        rprint("\n[yellow]Next steps:[/yellow]")
        rprint(f"1. [cyan]strandsflow server --config {config_file}[/cyan]")
        rprint(f"2. [cyan]strandsflow chat --config {config_file}[/cyan]")
        rprint(f"3. Visit [cyan]http://localhost:{port}/docs[/cyan] for API documentation")
        
        # Create example usage script
        example_script = f"""#!/usr/bin/env python3
\"\"\"
Example usage of your custom {agent_type} agent.
\"\"\"

import asyncio
import httpx

async def test_custom_agent():
    \"\"\"Test the custom agent via API.\"\"\"
    
    base_url = "http://localhost:{port}"
    
    # Test health check
    async with httpx.AsyncClient() as client:
        # Health check
        health = await client.get(f"{{base_url}}/health")
        print("Health:", health.json())
        
        # Agent info
        info = await client.get(f"{{base_url}}/agent/info")
        print("Agent Info:", info.json())
        
        # Chat example
        chat_response = await client.post(
            f"{{base_url}}/chat",
            json={{
                "content": "Hello! Can you introduce yourself and explain what you can help me with?",
                "session_id": "test-session"
            }}
        )
        print("Chat Response:", chat_response.json())

if __name__ == "__main__":
    print("Testing custom {agent_type} agent...")
    asyncio.run(test_custom_agent())
"""
        
        script_file = f"test_{agent_type.replace('-', '_')}_agent.py"
        with open(script_file, 'w') as f:
            f.write(example_script)
        
        rprint(f"[green]📝 Created example script: {script_file}[/green]")
        
    except Exception as e:
        rprint(f"[red]❌ Error creating custom agent: {e}[/red]")
        raise typer.Exit(1)


@multiagent_app.command("create")
def create_multiagent_setup(
    agents: str = typer.Option(
        "assistant,researcher",
        "--agents",
        "-a",
        help="Comma-separated list of agent types to create (e.g., assistant,researcher,analyst)"
    ),
    base_port: int = typer.Option(
        8000,
        "--base-port",
        "-p",
        help="Base port for agents (each agent gets port+1)"
    ),
    workspace: str = typer.Option(
        "multiagent_workspace",
        "--workspace",
        "-w",
        help="Directory to create agent configurations"
    ),
    model: str = typer.Option(
        "anthropic.claude-3-haiku-20240307-v1:0",
        "--model",
        "-m",
        help="Bedrock model ID for all agents"
    )
):
    """Create multiple agents configured for A2A communication."""
    
    try:
        # Parse agents list
        agent_list = [agent.strip() for agent in agents.split(",") if agent.strip()]
        
        if len(agent_list) < 2:
            rprint("[red]❌ Need at least 2 agents for multi-agent setup[/red]")
            raise typer.Exit(1)
        
        # Create workspace directory
        workspace_path = Path(workspace)
        workspace_path.mkdir(exist_ok=True)
        
        rprint(f"[blue]🏗️ Creating multi-agent setup in: {workspace_path}[/blue]")
        
        # Agent specializations
        agent_specializations = {
            "assistant": {
                "description": "General-purpose AI assistant for task coordination and user interaction",
                "system_prompt": """You are a helpful AI assistant that specializes in:
- Task coordination and delegation
- User interaction and communication
- General knowledge and problem-solving
- Coordinating with other specialist agents

When working with other agents, clearly communicate requirements and consolidate responses.""",
                "temperature": 0.7,
                "max_tokens": 4096
            },
            "researcher": {
                "description": "Research specialist for information gathering and analysis",
                "system_prompt": """You are a research specialist AI agent focusing on:
- Information gathering and fact-checking
- Market research and competitive analysis
- Academic research and literature review
- Data collection and verification

Provide thorough, well-sourced research with clear citations and methodology.""",
                "temperature": 0.3,
                "max_tokens": 6144
            },
            "analyst": {
                "description": "Data analysis and business intelligence expert",
                "system_prompt": """You are a data analysis expert specializing in:
- Statistical analysis and modeling
- Business intelligence and KPI analysis
- Trend identification and forecasting
- Data visualization and reporting

Always show your analytical process and provide actionable insights.""",
                "temperature": 0.2,
                "max_tokens": 8192
            },
            "writer": {
                "description": "Content creation and writing specialist",
                "system_prompt": """You are a professional writer and content specialist focusing on:
- Technical documentation and guides
- Marketing copy and communications
- Creative writing and storytelling
- Content optimization and editing

Create engaging, well-structured content adapted to your audience.""",
                "temperature": 0.8,
                "max_tokens": 6144
            },
            "coder": {
                "description": "Software development and code review specialist",
                "system_prompt": """You are a software engineer and coding expert specializing in:
- Code development and architecture
- Code review and optimization
- Debugging and troubleshooting
- Best practices and security

Write clean, efficient, well-documented code with proper error handling.""",
                "temperature": 0.2,
                "max_tokens": 8192
            }
        }
        
        created_agents = []
        agent_configs = {}
        
        for i, agent_type in enumerate(agent_list):
            port = base_port + i
            config_file = workspace_path / f"{agent_type}_config.yaml"
            
            # Get specialization or use default
            spec = agent_specializations.get(agent_type, {
                "description": f"Specialized {agent_type} agent",
                "system_prompt": f"You are a specialized {agent_type} AI agent. Help users with {agent_type}-related tasks.",
                "temperature": 0.5,
                "max_tokens": 4096
            })
            
            # Create agent configuration
            config_data = {
                "agent": {
                    "name": f"{agent_type.title()} Agent",
                    "description": spec["description"],
                    "enable_memory": True,
                    "max_conversation_turns": 50,
                    "system_prompt": spec["system_prompt"]
                },
                "api": {
                    "cors_origins": ["*"],
                    "host": "127.0.0.1",
                    "port": port,
                    "reload": False,
                    "workers": 1
                },
                "bedrock": {
                    "cache_prompt": None,
                    "cache_tools": None,
                    "guardrail_id": None,
                    "guardrail_trace": "enabled",
                    "guardrail_version": None,
                    "max_tokens": spec["max_tokens"],
                    "model_id": model,
                    "region_name": "us-west-2",
                    "stop_sequences": None,
                    "streaming": True,
                    "temperature": spec["temperature"],
                    "top_p": None
                },
                "mcp": {
                    "auto_discover": True,
                    "connection_timeout": 30,
                    "default_transport": "stdio",
                    "servers": {}
                },
                "environment": {
                    "name": "development",
                    "debug": True,
                    "log_level": "INFO",
                    "enable_metrics": True,
                    "rate_limit_requests": 60,
                    "max_concurrent_connections": 100
                },
                # A2A Configuration
                "a2a": {
                    "agent_id": f"{agent_type}_agent",
                    "server_port": port + 100,  # A2A server on separate port
                    "peers": []  # Will be populated with other agents
                }
            }
            
            # Write configuration
            import yaml
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            created_agents.append({
                "type": agent_type,
                "config_file": str(config_file),
                "api_port": port,
                "a2a_port": port + 100,
                "agent_id": f"{agent_type}_agent"
            })
            
            agent_configs[agent_type] = config_data
            
            rprint(f"[green]✅ Created {agent_type} agent: {config_file}[/green]")
        
        # Update all configs with peer information
        for agent in created_agents:
            config_file = Path(agent["config_file"])
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Add peer information
            peers = []
            for other_agent in created_agents:
                if other_agent["agent_id"] != agent["agent_id"]:
                    peers.append({
                        "agent_id": other_agent["agent_id"],
                        "endpoint": f"http://localhost:{other_agent['a2a_port']}"
                    })
            
            config_data["a2a"]["peers"] = peers
            
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
        
        # Create orchestrator configuration
        orchestrator_config = workspace_path / "orchestrator_config.yaml"
        orchestrator_data = {
            "orchestrator": {
                "name": "Multi-Agent Orchestrator",
                "agents": [
                    {
                        "agent_id": agent["agent_id"],
                        "type": agent["type"],
                        "endpoint": f"http://localhost:{agent['api_port']}",
                        "a2a_endpoint": f"http://localhost:{agent['a2a_port']}"
                    }
                    for agent in created_agents
                ],
                "routing_strategy": "round_robin",
                "max_retries": 3
            }
        }
        
        with open(orchestrator_config, 'w') as f:
            yaml.dump(orchestrator_data, f, default_flow_style=False, indent=2)
        
        # Create startup script
        startup_script = workspace_path / "start_agents.py"
        startup_code = f'''#!/usr/bin/env python3
"""
Multi-Agent Startup Script
Starts all agents and enables A2A communication.
"""

import asyncio
import subprocess
import time
import sys
from pathlib import Path

def start_agent_server(config_file, agent_type):
    """Start an agent server in the background."""
    cmd = [sys.executable, "-m", "strandsflow", "server", "--config", config_file]
    print(f"Starting {{agent_type}} agent: {{config_file}}")
    return subprocess.Popen(cmd)

async def main():
    """Start all agents and wait."""
    
    workspace = Path("{workspace}")
    processes = []
    
    agents = {json.dumps(agent_list)}
    
    try:
        # Start all agent servers
        for agent_type in agents:
            config_file = workspace / f"{{agent_type}}_config.yaml"
            if config_file.exists():
                process = start_agent_server(str(config_file), agent_type)
                processes.append(process)
                time.sleep(2)  # Stagger startup
        
        print(f"\\n🚀 Started {{len(processes)}} agents!")
        print("\\nAgent endpoints:")
        {chr(10).join([f'        print("  {agent["type"].title()}: http://localhost:{agent["api_port"]}")' for agent in created_agents])}
        
        print("\\nPress Ctrl+C to stop all agents...")
        
        # Wait for interrupt
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\\n🛑 Stopping all agents...")
        for process in processes:
            process.terminate()
        
        # Wait for clean shutdown
        for process in processes:
            process.wait()
        
        print("✅ All agents stopped.")

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        with open(startup_script, 'w') as f:
            f.write(startup_code)
        startup_script.chmod(0o755)
        
        # Create A2A communication test script
        test_script = workspace_path / "test_a2a_communication.py"
        test_code = f'''#!/usr/bin/env python3
"""
Test A2A Communication Between Agents
"""

import asyncio
import httpx
import json
from pathlib import Path

async def test_a2a_communication():
    """Test agent-to-agent communication."""
    
    agents = {json.dumps(created_agents)}
    
    print("🧪 Testing A2A Communication...")
    
    async with httpx.AsyncClient() as client:
        # Test each agent's health
        for agent in agents:
            try:
                response = await client.get(f"http://localhost:{{agent['api_port']}}/health")
                status = "✅" if response.status_code == 200 else "❌"
                print(f"{{status}} {{agent['type'].title()}} Agent (port {{agent['api_port']}})")
            except Exception as e:
                print(f"❌ {{agent['type'].title()}} Agent: {{e}}")
        
        # Test orchestrated communication
        print("\\n🤝 Testing orchestrated communication...")
        
        try:
            # Example: Get researcher to help assistant
            message = "I need research on the latest AI trends in 2024. Can you help?"
            
            response = await client.post(
                f"http://localhost:{created_agents[0]['api_port']}/multiagent/orchestrate",
                json={{
                    "task": message,
                    "required_agents": ["researcher"],
                    "session_id": "test-session"
                }}
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Orchestrated communication successful!")
                print(f"Response: {{result.get('response', 'No response')[:100]}}...")
            else:
                print(f"❌ Orchestration failed: {{response.status_code}}")
                
        except Exception as e:
            print(f"❌ Orchestration error: {{e}}")

if __name__ == "__main__":
    asyncio.run(test_a2a_communication())
'''
        
        with open(test_script, 'w') as f:
            f.write(test_code)
        test_script.chmod(0o755)
        
        # Create agent communication script
        chat_script = workspace_path / "agent_chat.py"
        chat_code = f'''#!/usr/bin/env python3
"""
Interactive Agent-to-Agent Chat Interface
"""

import asyncio
import httpx
import json
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

console = Console()

async def agent_chat():
    """Interactive chat interface for multi-agent communication."""
    
    agents = {json.dumps(created_agents)}
    
    console.print(Panel.fit("🤖 Multi-Agent Chat Interface", style="bold blue"))
    
    # Show available agents
    console.print("\\nAvailable agents:")
    for i, agent in enumerate(agents):
        console.print(f"  {{i+1}}. {{agent['type'].title()}} Agent (port {{agent['api_port']}})")
    
    while True:
        try:
            # Select source agent
            source_idx = int(Prompt.ask("\\nSelect source agent (number)")) - 1
            if source_idx < 0 or source_idx >= len(agents):
                console.print("[red]Invalid agent selection[/red]")
                continue
            
            source_agent = agents[source_idx]
            
            # Get message
            message = Prompt.ask(f"\\nMessage for {{source_agent['type'].title()}} Agent")
            
            if message.lower() in ['quit', 'exit', 'q']:
                break
            
            # Send message
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(
                        f"http://localhost:{{source_agent['api_port']}}/chat",
                        json={{
                            "content": message,
                            "session_id": "interactive-session"
                        }}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        console.print(f"\\n[green]{{source_agent['type'].title()}} Agent:[/green]")
                        console.print(Panel(result.get('response', 'No response')))
                    else:
                        console.print(f"[red]Error: {{response.status_code}}[/red]")
                        
                except Exception as e:
                    console.print(f"[red]Error: {{e}}[/red]")
                    
        except (KeyboardInterrupt, EOFError):
            break
        except ValueError:
            console.print("[red]Please enter a valid number[/red]")
    
    console.print("\\n👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(agent_chat())
'''
        
        with open(chat_script, 'w') as f:
            f.write(chat_code)
        chat_script.chmod(0o755)
        
        # Summary
        rprint(f"\n[green]🎉 Multi-agent setup complete![/green]")
        rprint(f"[blue]Workspace: {workspace_path}[/blue]")
        rprint(f"[blue]Agents created: {', '.join([agent['type'] for agent in created_agents])}[/blue]")
        
        # Display summary table
        table = Table(title="Created Agents")
        table.add_column("Agent Type", style="cyan")
        table.add_column("Config File", style="magenta")
        table.add_column("API Port", style="green")
        table.add_column("A2A Port", style="yellow")
        
        for agent in created_agents:
            table.add_row(
                agent["type"].title(),
                agent["config_file"],
                str(agent["api_port"]),
                str(agent["a2a_port"])
            )
        
        console.print(table)
        
        rprint("\n[yellow]Next steps:[/yellow]")
        rprint(f"1. [cyan]cd {workspace}[/cyan]")
        rprint(f"2. [cyan]python start_agents.py[/cyan] (start all agents)")
        rprint(f"3. [cyan]python agent_chat.py[/cyan] (interactive chat)")
        rprint(f"4. [cyan]python test_a2a_communication.py[/cyan] (test A2A)")
        
    except Exception as e:
        rprint(f"[red]❌ Error creating multi-agent setup: {e}[/red]")
        raise typer.Exit(1)


@multiagent_app.command("chat")
def multiagent_chat(
    workspace: str = typer.Option(
        "multiagent_workspace",
        "--workspace",
        "-w",
        help="Multi-agent workspace directory"
    ),
    agent1: Optional[str] = typer.Option(
        None,
        "--agent1",
        "-a1",
        help="First agent type for communication"
    ),
    agent2: Optional[str] = typer.Option(
        None,
        "--agent2",
        "-a2",
        help="Second agent type for communication"
    )
):
    """Start interactive A2A chat between two agents."""
    
    async def run_multiagent_chat():
        workspace_path = Path(workspace)
        
        if not workspace_path.exists():
            rprint(f"[red]❌ Workspace not found: {workspace}[/red]")
            rprint("Use 'strandsflow multiagent create' to create a workspace first.")
            raise typer.Exit(1)
        
        # Find available agents
        config_files = list(workspace_path.glob("*_config.yaml"))
        if not config_files:
            rprint(f"[red]❌ No agent configs found in {workspace}[/red]")
            raise typer.Exit(1)
        
        available_agents = []
        for config_file in config_files:
            agent_type = config_file.stem.replace("_config", "")
            if agent_type != "orchestrator":
                available_agents.append(agent_type)
        
        rprint(f"[blue]Available agents: {', '.join(available_agents)}[/blue]")
        
        # Initialize agent variables
        selected_agent1 = agent1
        selected_agent2 = agent2
        
        # Select agents if not provided
        if not selected_agent1:
            rprint("\\nSelect first agent:")
            for i, agent in enumerate(available_agents):
                rprint(f"  {i+1}. {agent}")
            
            try:
                idx = int(Prompt.ask("Choose agent (number)")) - 1
                selected_agent1 = available_agents[idx]
            except (ValueError, IndexError):
                rprint("[red]Invalid selection[/red]")
                raise typer.Exit(1)
        
        if not selected_agent2:
            remaining_agents = [a for a in available_agents if a != selected_agent1]
            if not remaining_agents:
                rprint("[red]❌ Need at least 2 agents for A2A chat[/red]")
                raise typer.Exit(1)
            
            rprint("\\nSelect second agent:")
            for i, agent in enumerate(remaining_agents):
                rprint(f"  {i+1}. {agent}")
            
            try:
                idx = int(Prompt.ask("Choose agent (number)")) - 1
                selected_agent2 = remaining_agents[idx]
            except (ValueError, IndexError):
                rprint("[red]Invalid selection[/red]")
                raise typer.Exit(1)
        
        # Load agent configurations
        config1_file = workspace_path / f"{selected_agent1}_config.yaml"
        config2_file = workspace_path / f"{selected_agent2}_config.yaml"
        
        if not config1_file.exists() or not config2_file.exists():
            rprint(f"[red]❌ Agent configs not found[/red]")
            raise typer.Exit(1)
        
        import yaml
        with open(config1_file) as f:
            config1 = yaml.safe_load(f)
        with open(config2_file) as f:
            config2 = yaml.safe_load(f)
        
        port1 = config1["api"]["port"]
        port2 = config2["api"]["port"]
        
        rprint(f"\\n[green]🤖 Starting A2A Chat: {selected_agent1.title()} ↔ {selected_agent2.title()}[/green]")
        rprint(f"[dim]Agent 1: {selected_agent1} (port {port1})[/dim]")
        rprint(f"[dim]Agent 2: {selected_agent2} (port {port2})[/dim]")
        
        # Check if agents are running
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                response1 = await client.get(f"http://localhost:{port1}/health")
                response2 = await client.get(f"http://localhost:{port2}/health")
                
                if response1.status_code != 200:
                    rprint(f"[red]❌ {selected_agent1} agent not running on port {port1}[/red]")
                    raise typer.Exit(1)
                
                if response2.status_code != 200:
                    rprint(f"[red]❌ {selected_agent2} agent not running on port {port2}[/red]")
                    raise typer.Exit(1)
                
            except httpx.ConnectError:
                rprint("[red]❌ Agents not running. Start them first with:[/red]")
                rprint(f"[yellow]cd {workspace} && python start_agents.py[/yellow]")
                raise typer.Exit(1)
        
        rprint("\\n[green]💬 A2A Chat Mode (type 'quit' to exit)[/green]")
        rprint("[dim]Format: [agent_name]: message or just message to alternate[/dim]")
        
        current_agent = selected_agent1
        session_id = f"a2a-chat-{int(time.time())}"
        
        while True:
            try:
                user_input = Prompt.ask(f"\\n[bold blue]Enter message for {current_agent.title()}[/bold blue]")
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not user_input.strip():
                    continue
                
                # Check if user wants to specify agent
                if ":" in user_input and any(agent in user_input.lower() for agent in [selected_agent1, selected_agent2]):
                    parts = user_input.split(":", 1)
                    specified_agent = parts[0].strip().lower()
                    message = parts[1].strip()
                    
                    if specified_agent == selected_agent1.lower():
                        current_agent = selected_agent1
                        port = port1
                    elif specified_agent == selected_agent2.lower():
                        current_agent = selected_agent2
                        port = port2
                    else:
                        message = user_input
                        port = port1 if current_agent == selected_agent1 else port2
                else:
                    message = user_input
                    port = port1 if current_agent == selected_agent1 else port2
                
                # Send message to current agent
                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.post(
                            f"http://localhost:{port}/chat",
                            json={
                                "content": message,
                                "session_id": session_id
                            }
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            agent_response = result.get('response', 'No response')
                            rprint(f"\\n[bold green]{current_agent.title()} Agent:[/bold green]")
                            rprint(agent_response)
                            
                            # Switch to other agent for next turn
                            current_agent = selected_agent2 if current_agent == selected_agent1 else selected_agent1
                            
                        else:
                            rprint(f"[red]❌ Error: {response.status_code}[/red]")
                            
                    except Exception as e:
                        rprint(f"[red]❌ Communication error: {e}[/red]")
                        
            except KeyboardInterrupt:
                break
            except EOFError:
                break
        
        rprint("\\n[dim]👋 A2A Chat ended![/dim]")
    
    asyncio.run(run_multiagent_chat())


@multiagent_app.command("orchestrate")
def orchestrate_agents(
    workspace: str = typer.Option(
        "multiagent_workspace",
        "--workspace",
        "-w",
        help="Multi-agent workspace directory"
    ),
    task: str = typer.Argument(..., help="Task to orchestrate across agents"),
    agents: Optional[List[str]] = typer.Option(
        None,
        "--agents",
        "-a",
        help="Specific agents to use (default: all available)"
    )
):
    """Orchestrate a task across multiple agents."""
    
    async def run_orchestration():
        workspace_path = Path(workspace)
        
        if not workspace_path.exists():
            rprint(f"[red]❌ Workspace not found: {workspace}[/red]")
            raise typer.Exit(1)
        
        # Load orchestrator config
        orchestrator_config = workspace_path / "orchestrator_config.yaml"
        if not orchestrator_config.exists():
            rprint(f"[red]❌ Orchestrator config not found: {orchestrator_config}[/red]")
            raise typer.Exit(1)
        
        import yaml
        with open(orchestrator_config) as f:
            config = yaml.safe_load(f)
        
        available_agents = config["orchestrator"]["agents"]
        
        # Filter agents if specified
        if agents:
            available_agents = [
                agent for agent in available_agents 
                if agent["type"] in agents
            ]
        
        if not available_agents:
            rprint("[red]❌ No agents available for orchestration[/red]")
            raise typer.Exit(1)
        
        rprint(f"[blue]🎭 Orchestrating task across {len(available_agents)} agents[/blue]")
        rprint(f"[dim]Task: {task}[/dim]")
        
        # Check agent availability
        import httpx
        async with httpx.AsyncClient() as client:
            for agent in available_agents:
                try:
                    response = await client.get(f"{agent['endpoint']}/health")
                    status = "✅" if response.status_code == 200 else "❌"
                    rprint(f"{status} {agent['type'].title()} Agent")
                except Exception:
                    rprint(f"❌ {agent['type'].title()} Agent (not running)")
        
        # Create simple orchestration (send task to each agent)
        results = {}
        
        for agent in available_agents:
            try:
                async with httpx.AsyncClient() as client:
                    rprint(f"\\n[yellow]📤 Sending task to {agent['type'].title()} Agent...[/yellow]")
                    
                    response = await client.post(
                        f"{agent['endpoint']}/chat",
                        json={
                            "content": f"Task: {task}\\n\\nPlease provide your specialized perspective on this task.",
                            "session_id": f"orchestration-{int(time.time())}"
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        agent_response = result.get('response', 'No response')
                        results[agent['type']] = agent_response
                        
                        rprint(f"[green]✅ Response from {agent['type'].title()}:[/green]")
                        rprint(f"[dim]{agent_response[:200]}{'...' if len(agent_response) > 200 else ''}[/dim]")
                    else:
                        rprint(f"[red]❌ Error from {agent['type']}: {response.status_code}[/red]")
                        
            except Exception as e:
                rprint(f"[red]❌ Error communicating with {agent['type']}: {e}[/red]")
        
        # Summary
        if results:
            rprint(f"\\n[green]🎯 Orchestration complete! Got {len(results)} responses.[/green]")
            
            # Create summary file
            summary_file = workspace_path / f"orchestration_results_{int(time.time())}.json"
            summary_data = {
                "task": task,
                "timestamp": time.time(),
                "agents": list(results.keys()),
                "results": results
            }
            
            with open(summary_file, 'w') as f:
                json.dump(summary_data, f, indent=2)
            
            rprint(f"[blue]📄 Results saved to: {summary_file}[/blue]")
        else:
            rprint("[red]❌ No responses received from agents[/red]")
    
    asyncio.run(run_orchestration())


if __name__ == "__main__":
    app()
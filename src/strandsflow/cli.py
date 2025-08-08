#!/usr/bin/env python3
"""
StrandsFlow CLI

Command-line interface for the StrandsFlow AI agent platform.
Provides tools for agent creation, configuration, and interaction.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich import print as rprint

from .core.config import StrandsFlowConfig
from .core.agent import StrandsFlowAgent

app = typer.Typer(
    name="strandsflow",
    help="StrandsFlow AI Agent Platform CLI",
    rich_markup_mode="rich"
)

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


if __name__ == "__main__":
    app()
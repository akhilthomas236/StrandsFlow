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
                response = await agent.chat_async(message)
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
                        response = await agent.chat_async(user_input)
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


if __name__ == "__main__":
    app()
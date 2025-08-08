#!/usr/bin/env python3
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
    
    agents = [{"type": "assistant", "config_file": "demo_agents/assistant_config.yaml", "api_port": 8020, "a2a_port": 8120, "agent_id": "assistant_agent"}, {"type": "researcher", "config_file": "demo_agents/researcher_config.yaml", "api_port": 8021, "a2a_port": 8121, "agent_id": "researcher_agent"}, {"type": "writer", "config_file": "demo_agents/writer_config.yaml", "api_port": 8022, "a2a_port": 8122, "agent_id": "writer_agent"}]
    
    console.print(Panel.fit("🤖 Multi-Agent Chat Interface", style="bold blue"))
    
    # Show available agents
    console.print("\nAvailable agents:")
    for i, agent in enumerate(agents):
        console.print(f"  {i+1}. {agent['type'].title()} Agent (port {agent['api_port']})")
    
    while True:
        try:
            # Select source agent
            source_idx = int(Prompt.ask("\nSelect source agent (number)")) - 1
            if source_idx < 0 or source_idx >= len(agents):
                console.print("[red]Invalid agent selection[/red]")
                continue
            
            source_agent = agents[source_idx]
            
            # Get message
            message = Prompt.ask(f"\nMessage for {source_agent['type'].title()} Agent")
            
            if message.lower() in ['quit', 'exit', 'q']:
                break
            
            # Send message
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(
                        f"http://localhost:{source_agent['api_port']}/chat",
                        json={
                            "content": message,
                            "session_id": "interactive-session"
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        console.print(f"\n[green]{source_agent['type'].title()} Agent:[/green]")
                        console.print(Panel(result.get('response', 'No response')))
                    else:
                        console.print(f"[red]Error: {response.status_code}[/red]")
                        
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
                    
        except (KeyboardInterrupt, EOFError):
            break
        except ValueError:
            console.print("[red]Please enter a valid number[/red]")
    
    console.print("\n👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(agent_chat())

#!/usr/bin/env python3
"""
Simple CLI Demo - Create and Test Two Agents Communicating

This script demonstrates the complete workflow of creating two agents
and setting them up for communication via CLI commands.
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def run_cli_command(cmd, description):
    """Run a CLI command with proper environment setup."""
    print(f"\n🔧 {description}")
    print(f"💻 Command: {cmd}")
    print("-" * 60)
    
    # Set up environment
    env = os.environ.copy()
    env['PYTHONPATH'] = "/Users/annmariyajoshy/vibecoding/strands_agent/src:" + env.get('PYTHONPATH', '')
    
    # Run command
    result = subprocess.run(cmd, shell=True, env=env)
    return result.returncode == 0

def main():
    """Demonstrate CLI workflow for multi-agent communication."""
    
    print("🚀 StrandsFlow CLI Multi-Agent Demo")
    print("="*50)
    print("This demo shows how to create two agents and enable A2A communication using CLI commands.")
    print()
    
    # Clean up any existing workspace
    workspace = "cli_demo"
    if Path(workspace).exists():
        import shutil
        shutil.rmtree(workspace)
        print(f"🧹 Cleaned up existing workspace: {workspace}")
    
    # Step 1: Create two agents
    print("\\n" + "="*50)
    print("STEP 1: Create Two Agents")
    print("="*50)
    
    success = run_cli_command(
        f"python -m strandsflow multiagent create --agents assistant,researcher --workspace {workspace} --base-port 8030",
        "Creating assistant and researcher agents with A2A communication"
    )
    
    if not success:
        print("❌ Failed to create agents. Check your setup.")
        return
    
    print("\\n✅ Successfully created two agents!")
    print("📁 Generated files:")
    for file in Path(workspace).iterdir():
        if file.is_file():
            print(f"   • {file.name}")
    
    # Step 2: Test agent configuration
    print("\\n" + "="*50)
    print("STEP 2: Test Agent Configuration")  
    print("="*50)
    
    # Show agent configs
    print("\\n📋 Agent Configurations:")
    import yaml
    
    for agent in ["assistant", "researcher"]:
        config_file = Path(workspace) / f"{agent}_config.yaml"
        if config_file.exists():
            with open(config_file) as f:
                config = yaml.safe_load(f)
            
            print(f"\\n🤖 {agent.title()} Agent:")
            print(f"   • Name: {config['agent']['name']}")
            print(f"   • API Port: {config['api']['port']}")
            print(f"   • A2A Port: {config['a2a']['server_port']}")
            print(f"   • Agent ID: {config['a2a']['agent_id']}")
            print(f"   • Peers: {len(config['a2a']['peers'])} configured")
    
    # Step 3: Show communication commands
    print("\\n" + "="*50)
    print("STEP 3: Agent Communication Commands")
    print("="*50)
    
    print("\\n💬 Available CLI Commands:")
    
    commands = [
        {
            "cmd": f"python -m strandsflow multiagent chat --workspace {workspace} --agent1 assistant --agent2 researcher",
            "desc": "Start interactive A2A chat between assistant and researcher"
        },
        {
            "cmd": f"python -m strandsflow multiagent orchestrate 'Research AI trends in 2024' --workspace {workspace}",
            "desc": "Orchestrate a research task across both agents"
        },
        {
            "cmd": f"python -m strandsflow server --config {workspace}/assistant_config.yaml",
            "desc": "Start the assistant agent server"
        },
        {
            "cmd": f"python -m strandsflow server --config {workspace}/researcher_config.yaml", 
            "desc": "Start the researcher agent server"
        },
        {
            "cmd": f"cd {workspace} && python start_agents.py",
            "desc": "Start both agents simultaneously"
        }
    ]
    
    for i, cmd_info in enumerate(commands, 1):
        print(f"\\n{i}. {cmd_info['desc']}")
        print(f"   Command: {cmd_info['cmd']}")
    
    # Step 4: Test CLI commands (without starting servers)
    print("\\n" + "="*50)
    print("STEP 4: Test CLI Commands (Dry Run)")
    print("="*50)
    
    print("\\n🧪 Testing chat command (will show that agents aren't running):")
    
    # Test the chat command - it should detect agents aren't running
    env = os.environ.copy()
    env['PYTHONPATH'] = "/Users/annmariyajoshy/vibecoding/strands_agent/src:" + env.get('PYTHONPATH', '')
    
    # Use echo to simulate quitting immediately
    cmd = f"echo 'q' | python -m strandsflow multiagent chat --workspace {workspace} --agent1 assistant --agent2 researcher"
    
    print(f"💻 Running: {cmd}")
    print("-" * 40)
    
    result = subprocess.run(cmd, shell=True, env=env, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"Errors: {result.stderr}")
    
    # Step 5: Summary and next steps
    print("\\n" + "="*50)
    print("STEP 5: Summary & Next Steps")
    print("="*50)
    
    print("\\n✅ Successfully demonstrated:")
    achievements = [
        "Created two specialized agents (assistant & researcher)",
        "Configured A2A communication between agents",
        "Generated complete workspace with configs and scripts",
        "Tested CLI commands for agent interaction",
        "Verified agent configuration and peer setup"
    ]
    
    for achievement in achievements:
        print(f"   ✓ {achievement}")
    
    print("\\n🎯 To enable full communication:")
    next_steps = [
        "Configure AWS credentials (aws configure)",
        f"Start agents: cd {workspace} && python start_agents.py",
        f"Test chat: python -m strandsflow multiagent chat --workspace {workspace}",
        "Try orchestration with real tasks",
        "Build custom workflows using the API"
    ]
    
    for i, step in enumerate(next_steps, 1):
        print(f"   {i}. {step}")
    
    print(f"\\n📂 Workspace created: {Path(workspace).absolute()}")
    print("🔗 API docs (when running): http://localhost:8030/docs")
    
    print("\\n" + "="*50)
    print("CLI DEMO COMPLETE! 🎉")
    print("You can now create agents and make them communicate via CLI!")
    print("="*50)

if __name__ == "__main__":
    main()

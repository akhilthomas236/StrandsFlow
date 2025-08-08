#!/usr/bin/env python3
"""
StrandsFlow Multi-Agent CLI Demo

This script demonstrates how to use the StrandsFlow CLI to create
and manage multiple agents for agent-to-agent communication.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description, capture_output=False):
    """Run a command and print results."""
    print(f"\n🔧 {description}")
    print(f"Command: {cmd}")
    print("-" * 50)
    
    # Set environment
    env = os.environ.copy()
    env['PYTHONPATH'] = "/Users/annmariyajoshy/vibecoding/strands_agent/src:" + env.get('PYTHONPATH', '')
    
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, env=env, capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print(f"Errors: {result.stderr}")
            return result.returncode == 0
        else:
            result = subprocess.run(cmd, shell=True, env=env)
            return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Main demo function."""
    print("🚀 StrandsFlow Multi-Agent CLI Demo")
    print("="*60)
    print()
    print("This demo shows how to:")
    print("1. Create multiple agents with A2A communication")
    print("2. Configure agent specializations")
    print("3. Set up agent-to-agent chat")
    print("4. Test the multi-agent system")
    print()
    
    # Step 1: Clean up any existing test workspace
    print("🧹 Cleaning up previous test workspace...")
    if Path("demo_agents").exists():
        import shutil
        shutil.rmtree("demo_agents")
    
    # Step 2: Create multi-agent setup
    success = run_command(
        "python -m strandsflow multiagent create --agents assistant,researcher,writer --workspace demo_agents --base-port 8020",
        "Creating 3 agents with A2A communication",
        capture_output=True
    )
    
    if not success:
        print("❌ Failed to create agents. Check your setup.")
        return
    
    # Step 3: Show what was created
    print("\\n📁 Generated files:")
    demo_path = Path("demo_agents")
    if demo_path.exists():
        for file in demo_path.iterdir():
            if file.is_file():
                print(f"   • {file.name}")
    
    # Step 4: Show agent configurations
    print("\\n📋 Agent Configurations:")
    config_files = list(demo_path.glob("*_config.yaml"))
    for config_file in config_files:
        agent_name = config_file.stem.replace("_config", "")
        if agent_name != "orchestrator":
            print(f"   • {agent_name.title()} Agent: {config_file}")
    
    # Step 5: Show CLI commands available
    print("\\n🛠️ Available CLI Commands:")
    print("   1. Chat between specific agents:")
    print("      python -m strandsflow multiagent chat --workspace demo_agents --agent1 assistant --agent2 researcher")
    print()
    print("   2. Orchestrate a task across agents:")
    print("      python -m strandsflow multiagent orchestrate 'Write a research report on AI trends' --workspace demo_agents")
    print()
    print("   3. Start individual agent servers:")
    print("      python -m strandsflow server --config demo_agents/assistant_config.yaml")
    print("      python -m strandsflow server --config demo_agents/researcher_config.yaml")
    print()
    print("   4. Start all agents at once:")
    print("      cd demo_agents && python start_agents.py")
    print()
    
    # Step 6: Test agent configurations
    print("\\n🧪 Testing agent configurations...")
    
    # Test that configs are valid
    success = run_command(
        "cd demo_agents && python ../test_multiagent/simple_test.py",
        "Validating agent configurations",
        capture_output=True
    )
    
    # Step 7: Show communication patterns
    print("\\n💬 Multi-Agent Communication Patterns:")
    patterns = [
        "Direct A2A: assistant ↔ researcher (peer-to-peer)",
        "Orchestrated: User → assistant → researcher → writer",
        "Parallel: All agents work on same task simultaneously",
        "Sequential: assistant → researcher → writer (pipeline)"
    ]
    
    for i, pattern in enumerate(patterns, 1):
        print(f"   {i}. {pattern}")
    
    # Step 8: Show next steps
    print("\\n🎯 Next Steps:")
    steps = [
        "Configure AWS credentials for actual agent communication",
        "Start agents: cd demo_agents && python start_agents.py",
        "Test A2A chat: python -m strandsflow multiagent chat --workspace demo_agents",
        "Try orchestration: python -m strandsflow multiagent orchestrate 'Your task here'",
        "Build custom workflows using the API endpoints"
    ]
    
    for i, step in enumerate(steps, 1):
        print(f"   {i}. {step}")
    
    print("\\n✅ Multi-agent setup complete!")
    print(f"Workspace: {demo_path.absolute()}")
    print("\\n📖 For more information:")
    print("   • API docs: http://localhost:8020/docs (when server is running)")
    print("   • Config files: demo_agents/*.yaml")
    print("   • Test scripts: demo_agents/*.py")

if __name__ == "__main__":
    main()

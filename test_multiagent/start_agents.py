#!/usr/bin/env python3
"""
Multi-Agent Startup Script
Starts all agents and enables A2A communication.
"""

import asyncio
import subprocess
import time
import sys
import os
from pathlib import Path

def start_agent_server(config_file, agent_type):
    """Start an agent server in the background."""
    env = os.environ.copy()
    env['PYTHONPATH'] = "/Users/annmariyajoshy/vibecoding/strands_agent/src:" + env.get('PYTHONPATH', '')
    cmd = [sys.executable, "-m", "strandsflow", "server", "--config", config_file]
    print(f"Starting {agent_type} agent: {config_file}")
    return subprocess.Popen(cmd, env=env)

async def main():
    """Start all agents and wait."""
    
    workspace = Path("test_multiagent")
    processes = []
    
    agents = ["assistant", "researcher"]
    
    try:
        # Start all agent servers
        for agent_type in agents:
            config_file = workspace / f"{agent_type}_config.yaml"
            if config_file.exists():
                process = start_agent_server(str(config_file), agent_type)
                processes.append(process)
                time.sleep(2)  # Stagger startup
        
        print(f"\n🚀 Started {len(processes)} agents!")
        print("\nAgent endpoints:")
        print("  Assistant: http://localhost:8010")
        print("  Researcher: http://localhost:8011")
        
        print("\nPress Ctrl+C to stop all agents...")
        
        # Wait for interrupt
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping all agents...")
        for process in processes:
            process.terminate()
        
        # Wait for clean shutdown
        for process in processes:
            process.wait()
        
        print("✅ All agents stopped.")

if __name__ == "__main__":
    asyncio.run(main())

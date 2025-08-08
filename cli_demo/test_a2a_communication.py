#!/usr/bin/env python3
"""
Test A2A Communication Between Agents
"""

import asyncio
import httpx
import json
from pathlib import Path

async def test_a2a_communication():
    """Test agent-to-agent communication."""
    
    agents = [{"type": "assistant", "config_file": "cli_demo/assistant_config.yaml", "api_port": 8030, "a2a_port": 8130, "agent_id": "assistant_agent"}, {"type": "researcher", "config_file": "cli_demo/researcher_config.yaml", "api_port": 8031, "a2a_port": 8131, "agent_id": "researcher_agent"}]
    
    print("🧪 Testing A2A Communication...")
    
    async with httpx.AsyncClient() as client:
        # Test each agent's health
        for agent in agents:
            try:
                response = await client.get(f"http://localhost:{agent['api_port']}/health")
                status = "✅" if response.status_code == 200 else "❌"
                print(f"{status} {agent['type'].title()} Agent (port {agent['api_port']})")
            except Exception as e:
                print(f"❌ {agent['type'].title()} Agent: {e}")
        
        # Test orchestrated communication
        print("\n🤝 Testing orchestrated communication...")
        
        try:
            # Example: Get researcher to help assistant
            message = "I need research on the latest AI trends in 2024. Can you help?"
            
            response = await client.post(
                f"http://localhost:8030/multiagent/orchestrate",
                json={
                    "task": message,
                    "required_agents": ["researcher"],
                    "session_id": "test-session"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Orchestrated communication successful!")
                print(f"Response: {result.get('response', 'No response')[:100]}...")
            else:
                print(f"❌ Orchestration failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Orchestration error: {e}")

if __name__ == "__main__":
    asyncio.run(test_a2a_communication())

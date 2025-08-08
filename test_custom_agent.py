#!/usr/bin/env python3
"""
Example usage of your custom custom agent.
"""

import asyncio
import httpx

async def test_custom_agent():
    """Test the custom agent via API."""
    
    base_url = "http://localhost:8001"
    
    # Test health check
    async with httpx.AsyncClient() as client:
        # Health check
        health = await client.get(f"{base_url}/health")
        print("Health:", health.json())
        
        # Agent info
        info = await client.get(f"{base_url}/agent/info")
        print("Agent Info:", info.json())
        
        # Chat example
        chat_response = await client.post(
            f"{base_url}/chat",
            json={
                "content": "Hello! Can you introduce yourself and explain what you can help me with?",
                "session_id": "test-session"
            }
        )
        print("Chat Response:", chat_response.json())

if __name__ == "__main__":
    print("Testing custom custom agent...")
    asyncio.run(test_custom_agent())

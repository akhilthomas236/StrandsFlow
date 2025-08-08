#!/usr/bin/env python3
"""
Simple test to verify Strands SDK integration.
Run with: python -m test_strands
"""

import asyncio
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from strandsflow.core.config import StrandsFlowConfig
from strandsflow.core.agent import StrandsFlowAgent


async def test_basic_agent():
    """Test basic StrandsFlow agent functionality."""
    print("🚀 Testing StrandsFlow Agent with Strands SDK...")
    
    # Create configuration
    config = StrandsFlowConfig(
        agent_name="Test Agent",
        bedrock_model_id="anthropic.claude-sonnet-4-20250514-v1:0"
    )
    
    print(f"✅ Configuration created: {config.agent_name}")
    
    # Create agent
    agent = StrandsFlowAgent(config=config)
    print(f"✅ Agent created with model: {config.bedrock_model_id}")
    
    # Initialize agent
    await agent.initialize()
    print(f"✅ Agent initialized successfully")
    
    # Test a simple chat
    try:
        response = await agent.chat("Hello! What's 2 + 2?")
        print(f"✅ Chat response: {response[:100]}...")
        
    except Exception as e:
        print(f"⚠️ Chat test failed (expected without AWS credentials): {e}")
    
    # Test metrics
    metrics = agent.get_metrics()
    print(f"✅ Agent metrics: {metrics}")
    
    # Shutdown
    await agent.shutdown()
    print("✅ Agent shutdown complete")
    
    print("\n🎉 StrandsFlow basic test completed!")


if __name__ == "__main__":
    asyncio.run(test_basic_agent())

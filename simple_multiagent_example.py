"""
Simple Multi-Agent Setup Example for StrandsFlow

This script demonstrates the basic setup and usage of StrandsFlow's
multi-agent system without requiring AWS credentials.
"""

import asyncio
import sys
import os

# Add the source directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


async def simple_multiagent_setup():
    """Demonstrate basic multi-agent setup without actual API calls."""
    print("🤖 Simple Multi-Agent Setup")
    print("=" * 40)
    
    try:
        # Import required modules
        from strandsflow.multiagent import (
            SpecialistPool, A2AServerManager, Orchestrator, WorkflowType
        )
        from strandsflow.core.config import StrandsFlowConfig
        from strandsflow.core.agent import StrandsFlowAgent
        
        print("✓ All modules imported successfully")
        
        # Step 1: Create configuration
        config = StrandsFlowConfig()
        print(f"✓ Configuration created (Model: {config.bedrock.model_id})")
        
        # Step 2: Create specialist pool
        print("\n📚 Creating Specialist Pool...")
        pool = SpecialistPool()
        
        # Define specialists with their roles and capabilities
        specialists_config = {
            "Math Expert": {
                "role": "Mathematics Specialist",
                "capabilities": ["calculations", "statistics", "problem_solving"],
                "system_prompt": "You are a mathematics expert. Solve problems step by step with clear explanations."
            },
            "Code Expert": {
                "role": "Software Engineer", 
                "capabilities": ["programming", "debugging", "code_review"],
                "system_prompt": "You are a senior software engineer. Write clean, efficient code with best practices."
            },
            "Writer": {
                "role": "Content Writer",
                "capabilities": ["writing", "editing", "communication"],
                "system_prompt": "You are a professional content writer. Create clear, engaging content."
            }
        }
        
        # Create and add specialists
        for name, spec in specialists_config.items():
            # Import the specialist config class
            from strandsflow.multiagent.specialist_pool import SpecialistConfig
            
            # Create specialist configuration
            specialist_config = SpecialistConfig(
                name=name,
                role=spec["role"],
                description=f"AI {spec['role']} specializing in {', '.join(spec['capabilities'])}",
                capabilities=spec["capabilities"],
                system_prompt=spec["system_prompt"],
                model_id="anthropic.claude-3-haiku-20240307-v1:0",  # Faster model
                temperature=0.7
            )
            
            # Create base config
            base_config = StrandsFlowConfig()
            
            # Add to pool
            agent = await pool.add_specialist(
                config=specialist_config,
                base_config=base_config
            )
            
            print(f"  ✓ Added {name}")
        
        print(f"✓ Created {len(pool.specialists)} specialists")
        
        # Step 3: Create orchestrator first  
        print("\n🎭 Creating Orchestrator...")
        a2a_manager = A2AServerManager()
        orchestrator = Orchestrator(a2a_manager=a2a_manager)
        
        # Add specialists to orchestrator (this handles A2A registration)
        for name, agent in pool.specialists.items():
            config_obj = pool.configs[name]
            orchestrator.add_specialist(
                name, agent, config_obj.role, config_obj.capabilities
            )
            print(f"  ✓ Added {name} to orchestrator and A2A network")
        
        # Create orchestrator agent (this creates the tools for routing)
        orchestrator.create_orchestrator_agent()
        print("✓ Orchestrator agent created with specialist tools")
        
        # Step 4: Demonstrate task routing (without actual execution)
        print("\n🧠 Task Routing Examples...")
        
        sample_tasks = [
            "Calculate the compound interest for $1000 at 5% for 3 years",
            "Write a Python function to sort a list of dictionaries", 
            "Write a blog post about renewable energy benefits",
            "Debug this code that has a memory leak issue"
        ]
        
        for task in sample_tasks:
            # Simulate routing decision based on task content
            if any(word in task.lower() for word in ["calculate", "interest", "math"]):
                routed_to = "Math Expert"
            elif any(word in task.lower() for word in ["python", "code", "function", "debug"]):
                routed_to = "Code Expert"
            elif any(word in task.lower() for word in ["write", "blog", "post", "content"]):
                routed_to = "Writer"
            else:
                routed_to = "Code Expert"  # Default
            
            print(f"  📝 Task: {task}")
            print(f"     → Routed to: {routed_to}")
            print()
        
        # Step 5: Show available workflows
        print("📋 Available Multi-Agent Patterns...")
        patterns = [
            "Conditional Routing: Route tasks to best specialist based on content",
            "Parallel Processing: Multiple agents work on same task simultaneously", 
            "Sequential Pipeline: Agents process task in order (research → write → review)",
            "Hierarchical: Master agent coordinates team of specialists"
        ]
        
        for i, pattern in enumerate(patterns, 1):
            print(f"  {i}. {pattern}")
        
        # Step 6: Configuration summary
        print("\n⚙️ Configuration Summary...")
        print(f"  • Total Specialists: {len(pool.specialists)}")
        print(f"  • A2A Servers: {len(a2a_manager.servers)}")
        print(f"  • Orchestrator Tools: {len(orchestrator.specialist_tools) if hasattr(orchestrator, 'specialist_tools') else 'Not created'}")
        print(f"  • Model: {config.bedrock.model_id}")
        
        # List all specialists and their capabilities
        print("\n👥 Specialist Directory:")
        specialists = pool.list_specialists()
        for name, info in specialists.items():
            print(f"  • {name}")
            print(f"    Role: {info['role']}")
            print(f"    Capabilities: {', '.join(info['capabilities'])}")
            print()
        
        print("🎉 Multi-agent setup completed successfully!")
        print("\nNext steps:")
        print("1. Configure AWS credentials to enable actual agent communication")
        print("2. Start the server: `strandsflow server`")
        print("3. Visit http://localhost:8000/docs for API documentation")
        print("4. Try the full demo: `python demo_multiagent.py`")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()


async def show_api_integration():
    """Show how to integrate with the API."""
    print("\n" + "=" * 50)
    print("🌐 API Integration Examples")
    print("=" * 50)
    
    api_examples = [
        {
            "endpoint": "POST /api/v1/multiagent/orchestrate",
            "description": "Route a task to the best specialist",
            "example": {
                "task": "Create a Python web scraper for product prices",
                "workflow_type": "conditional"
            }
        },
        {
            "endpoint": "GET /api/v1/multiagent/specialists", 
            "description": "List all available specialists",
            "example": "No request body needed"
        },
        {
            "endpoint": "POST /api/v1/multiagent/workflows/execute",
            "description": "Execute a predefined workflow",
            "example": {
                "workflow_name": "content_creation",
                "inputs": {
                    "topic": "AI in Healthcare",
                    "audience": "medical professionals"
                }
            }
        }
    ]
    
    for api in api_examples:
        print(f"\n📡 {api['endpoint']}")
        print(f"   {api['description']}")
        print(f"   Example: {api['example']}")
    
    print("\n🚀 To start the API server:")
    print("   strandsflow server --port 8000")
    print("\n📖 API Documentation:")
    print("   http://localhost:8000/docs")


if __name__ == "__main__":
    print("🚀 StrandsFlow Multi-Agent System Setup")
    print("Built on Strands Agents SDK with A2A Communication")
    print("=" * 60)
    
    asyncio.run(simple_multiagent_setup())
    asyncio.run(show_api_integration())

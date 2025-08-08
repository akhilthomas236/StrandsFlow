"""
Demo script showcasing StrandsFlow multi-agent capabilities.

This script demonstrates:
1. Creating specialist agents
2. A2A (Agent-to-Agent) communication
3. Multi-agent orchestration patterns
4. Workflow execution
5. Complex multi-agent tasks
"""

import asyncio
import sys
import os
import time

# Add the source directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def demo_basic_multiagent():
    """Demonstrate basic multi-agent functionality."""
    print("🤖 StrandsFlow Multi-Agent Demo")
    print("=" * 50)
    
    try:
        # Import core modules
        from strandsflow.core.config import StrandsFlowConfig
        from strandsflow.core.agent import StrandsFlowAgent
        
        print("✓ Core modules imported")
        
        # Check if multi-agent features are available
        try:
            from strandsflow.multiagent import (
                A2AServerManager, create_predefined_pool,
                Orchestrator, WorkflowManager, WorkflowType
            )
            print("✓ Multi-agent modules imported")
        except ImportError as e:
            print(f"⚠️  Multi-agent features not available: {e}")
            return
        
        # Create configuration
        config = StrandsFlowConfig()
        print(f"✓ Configuration loaded (Model: {config.bedrock.model_id})")
        
        # Create specialist pool
        print("\n📚 Creating Specialist Pool...")
        pool = await create_predefined_pool(config)
        print(f"✓ Created {len(pool.specialists)} specialist agents:")
        
        specialists = pool.list_specialists()
        for name, info in specialists.items():
            print(f"  • {name}: {info['role']}")
            print(f"    Capabilities: {', '.join(info['capabilities'])}")
        
        # Initialize specialists
        print("\n🔧 Initializing specialists...")
        await pool.initialize_all()
        print("✓ All specialists initialized")
        
        # Test individual specialist
        print("\n💬 Testing individual specialist...")
        code_expert = pool.get_specialist("Code Expert")
        if code_expert:
            response = await code_expert.chat("What are the SOLID principles in software development?")
            print(f"Code Expert: {response[:200]}...")
        
        # Create A2A manager
        print("\n🔗 Setting up A2A communication...")
        a2a_manager = A2AServerManager()
        
        # Add specialists to A2A manager
        for name, agent in pool.specialists.items():
            a2a_server = a2a_manager.add_agent(agent, name)
            print(f"✓ Added {name} to A2A network")
        
        # Create orchestrator
        print("\n🎭 Creating orchestrator...")
        orchestrator = Orchestrator(a2a_manager=a2a_manager)
        
        # Add specialists to orchestrator
        for name, agent in pool.specialists.items():
            config_obj = pool.configs[name]
            orchestrator.add_specialist(name, agent, config_obj.role, config_obj.capabilities)
        
        # Create orchestrator agent
        orchestrator.create_orchestrator_agent()
        print("✓ Orchestrator ready with all specialist tools")
        
        # Test orchestrator routing
        print("\n🧠 Testing intelligent task routing...")
        task = "I need help writing a Python function that analyzes sales data and creates a report."
        
        result = await orchestrator.execute_workflow(
            task=task,
            workflow_type=WorkflowType.CONDITIONAL
        )
        
        print(f"✓ Orchestrator routed task:")
        print(f"  Task: {task}")
        print(f"  Result: {result['routing_decision'][:200]}...")
        
        # Test workflow manager
        print("\n📋 Testing workflow manager...")
        workflow_manager = WorkflowManager(orchestrator, pool)
        
        workflows = workflow_manager.list_workflows()
        print(f"✓ Available workflows: {list(workflows.keys())}")
        
        # Cleanup
        print("\n🧹 Cleaning up...")
        await pool.shutdown_all()
        print("✓ All specialists shutdown")
        
        print("\n🎉 Multi-agent demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


async def demo_workflow_execution():
    """Demonstrate workflow execution."""
    print("\n" + "=" * 50)
    print("📋 Workflow Execution Demo")
    print("=" * 50)
    
    try:
        from strandsflow.multiagent import (
            WorkflowManager, Orchestrator, A2AServerManager,
            create_predefined_pool, WorkflowDefinition, WorkflowStep
        )
        from strandsflow.core.config import StrandsFlowConfig
        
        # Setup
        config = StrandsFlowConfig()
        pool = await create_predefined_pool(config)
        await pool.initialize_all()
        
        a2a_manager = A2AServerManager()
        orchestrator = Orchestrator(a2a_manager=a2a_manager)
        
        # Add specialists
        for name, agent in pool.specialists.items():
            config_obj = pool.configs[name]
            orchestrator.add_specialist(name, agent, config_obj.role, config_obj.capabilities)
        
        # Create workflow manager
        workflow_manager = WorkflowManager(orchestrator, pool)
        
        # Demo: Execute a content creation workflow
        print("\n📝 Starting content creation workflow...")
        
        inputs = {
            "topic": "The future of AI in software development",
            "audience": "software developers and technical managers"
        }
        
        execution_id = await workflow_manager.execute_workflow(
            workflow_name="content_creation",
            inputs=inputs
        )
        
        print(f"✓ Workflow started with ID: {execution_id}")
        
        # Monitor execution
        print("\n⏳ Monitoring workflow execution...")
        
        for i in range(30):  # Wait up to 30 seconds
            await asyncio.sleep(1)
            
            execution = workflow_manager.get_execution_status(execution_id)
            if execution:
                print(f"  Status: {execution.status.value} | Current step: {execution.current_step}")
                
                if execution.status.value in ["completed", "failed"]:
                    break
        
        # Get final results
        final_execution = workflow_manager.get_execution_status(execution_id)
        if final_execution:
            print(f"\n✓ Workflow {final_execution.status.value}")
            
            if final_execution.status.value == "completed":
                print("📊 Results:")
                if final_execution.results and "steps" in final_execution.results:
                    for step_name, step_result in final_execution.results["steps"].items():
                        if isinstance(step_result, dict) and "output" in step_result:
                            print(f"  {step_name}: {step_result['output'][:100]}...")
        
        # Cleanup
        await pool.shutdown_all()
        
    except Exception as e:
        print(f"❌ Workflow demo failed: {e}")
        import traceback
        traceback.print_exc()


async def demo_parallel_agents():
    """Demonstrate parallel agent execution."""
    print("\n" + "=" * 50)
    print("⚡ Parallel Agent Execution Demo")
    print("=" * 50)
    
    try:
        from strandsflow.multiagent import (
            Orchestrator, WorkflowType, A2AServerManager,
            create_predefined_pool
        )
        from strandsflow.core.config import StrandsFlowConfig
        
        # Setup
        config = StrandsFlowConfig()
        pool = await create_predefined_pool(config)
        await pool.initialize_all()
        
        a2a_manager = A2AServerManager()
        orchestrator = Orchestrator(a2a_manager=a2a_manager)
        
        # Add specialists
        for name, agent in pool.specialists.items():
            config_obj = pool.configs[name]
            orchestrator.add_specialist(name, agent, config_obj.role, config_obj.capabilities)
        
        # Test parallel execution
        task = "Analyze the pros and cons of microservices architecture"
        agents = ["Code Expert", "Research Assistant"]
        
        print(f"📝 Task: {task}")
        print(f"👥 Agents: {', '.join(agents)}")
        
        start_time = time.time()
        
        result = await orchestrator.execute_workflow(
            task=task,
            workflow_type=WorkflowType.PARALLEL,
            agents=agents
        )
        
        execution_time = time.time() - start_time
        
        print(f"⏱️  Execution time: {execution_time:.2f} seconds")
        print(f"✓ Parallel execution completed")
        
        if "results" in result:
            for agent_result in result["results"]:
                agent_name = agent_result.get("agent", "Unknown")
                output = agent_result.get("output", "No output")
                print(f"\n{agent_name}:")
                print(f"  {output[:150]}...")
        
        # Cleanup
        await pool.shutdown_all()
        
    except Exception as e:
        print(f"❌ Parallel demo failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all demos."""
    print("🚀 StrandsFlow Multi-Agent System Demonstration")
    print("Built on Strands Agents SDK with A2A Communication")
    print("=" * 60)
    
    demos = [
        ("Basic Multi-Agent Setup", demo_basic_multiagent),
        ("Workflow Execution", demo_workflow_execution),
        ("Parallel Agent Execution", demo_parallel_agents)
    ]
    
    for demo_name, demo_func in demos:
        print(f"\n🎬 Running: {demo_name}")
        print("-" * 40)
        
        try:
            await demo_func()
            print(f"✅ {demo_name} completed successfully")
        except Exception as e:
            print(f"❌ {demo_name} failed: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 All demos completed!")
    print("Visit http://localhost:8000/docs for API documentation")
    print("Use `strandsflow server` to start the multi-agent API server")


if __name__ == "__main__":
    asyncio.run(main())

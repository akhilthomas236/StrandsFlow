"""Test multi-agent functionality in StrandsFlow."""

import asyncio
import pytest
import sys
import os

# Add the source directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Test if imports work
def test_imports():
    """Test that all multi-agent modules can be imported."""
    try:
        import strandsflow
        print(f"✓ StrandsFlow version: {strandsflow.__version__}")
        
        from strandsflow.core.config import StrandsFlowConfig
        from strandsflow.core.agent import StrandsFlowAgent
        print("✓ Core modules imported successfully")
        
        # Test multi-agent imports
        if strandsflow.MULTIAGENT_AVAILABLE:
            from strandsflow.multiagent import (
                A2AServer, A2AServerManager, A2AClient,
                Orchestrator, WorkflowType,
                SpecialistPool, SpecialistConfig, create_predefined_pool,
                WorkflowManager
            )
            print("✓ Multi-agent modules imported successfully")
            return True
        else:
            print("⚠ Multi-agent modules not available - missing dependencies")
            return False
            
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


async def test_specialist_pool():
    """Test specialist pool functionality."""
    try:
        from strandsflow.multiagent import create_predefined_pool
        from strandsflow.core.config import StrandsFlowConfig
        
        print("\n=== Testing Specialist Pool ===")
        
        # Create base config
        config = StrandsFlowConfig()
        
        # Create predefined specialist pool
        pool = await create_predefined_pool(config)
        print(f"✓ Created specialist pool with {len(pool.specialists)} specialists")
        
        # List specialists
        specialists = pool.list_specialists()
        for name, info in specialists.items():
            print(f"  - {name}: {info['role']} ({info['model_id']})")
        
        # Test capability search
        code_specialists = pool.find_specialists_by_capability("programming")
        print(f"✓ Found {len(code_specialists)} programming specialists: {code_specialists}")
        
        data_specialists = pool.find_specialists_by_capability("data_analysis")
        print(f"✓ Found {len(data_specialists)} data analysis specialists: {data_specialists}")
        
        return True
        
    except Exception as e:
        print(f"✗ Specialist pool test failed: {e}")
        return False


async def test_a2a_server():
    """Test A2A server functionality."""
    try:
        from strandsflow.multiagent import A2AServerManager
        from strandsflow.core.agent import StrandsFlowAgent
        from strandsflow.core.config import StrandsFlowConfig
        
        print("\n=== Testing A2A Server ===")
        
        # Create a test agent
        config = StrandsFlowConfig()
        config.agent.name = "Test Agent"
        config.agent.description = "A test agent for A2A communication"
        
        agent = StrandsFlowAgent(config)
        
        # Create A2A manager
        a2a_manager = A2AServerManager()
        
        # Add agent to A2A manager
        a2a_server = a2a_manager.add_agent(agent, "test_agent")
        print(f"✓ Created A2A server for agent: {a2a_server.name}")
        
        # Get agent card
        card = a2a_server.get_card()
        print(f"✓ Agent card: {card['name']} - {card['description']}")
        
        # List all agents
        agents = a2a_manager.list_agents()
        print(f"✓ A2A agents registered: {list(agents.keys())}")
        
        # Test agent tools
        tools = a2a_manager.get_agent_tools()
        print(f"✓ Available agent tools: {len(tools)}")
        
        return True
        
    except Exception as e:
        print(f"✗ A2A server test failed: {e}")
        return False


async def test_orchestrator():
    """Test orchestrator functionality."""
    try:
        from strandsflow.multiagent import (
            Orchestrator, WorkflowType, A2AServerManager,
            create_predefined_pool
        )
        from strandsflow.core.config import StrandsFlowConfig
        
        print("\n=== Testing Orchestrator ===")
        
        # Create components
        config = StrandsFlowConfig()
        pool = await create_predefined_pool(config)
        a2a_manager = A2AServerManager()
        
        # Create orchestrator
        orchestrator = Orchestrator(a2a_manager=a2a_manager)
        
        # Add specialists
        for name, agent in pool.specialists.items():
            config_obj = pool.configs[name]
            orchestrator.add_specialist(name, agent, config_obj.role, config_obj.capabilities)
        
        print(f"✓ Added {len(orchestrator.agents)} specialists to orchestrator")
        
        # Create orchestrator agent
        orch_agent = orchestrator.create_orchestrator_agent()
        print("✓ Created orchestrator agent")
        
        # Test workflow types
        workflow_types = [WorkflowType.SEQUENTIAL, WorkflowType.PARALLEL, WorkflowType.CONDITIONAL]
        for wf_type in workflow_types:
            print(f"✓ Workflow type available: {wf_type.value}")
        
        # Get metrics
        metrics = orchestrator.get_metrics()
        print(f"✓ Orchestrator metrics: {metrics}")
        
        return True
        
    except Exception as e:
        print(f"✗ Orchestrator test failed: {e}")
        return False


async def test_workflow_manager():
    """Test workflow manager functionality."""
    try:
        from strandsflow.multiagent import (
            WorkflowManager, Orchestrator, A2AServerManager,
            create_predefined_pool
        )
        from strandsflow.core.config import StrandsFlowConfig
        
        print("\n=== Testing Workflow Manager ===")
        
        # Create components
        config = StrandsFlowConfig()
        pool = await create_predefined_pool(config)
        a2a_manager = A2AServerManager()
        orchestrator = Orchestrator(a2a_manager=a2a_manager)
        
        # Add specialists to orchestrator
        for name, agent in pool.specialists.items():
            config_obj = pool.configs[name]
            orchestrator.add_specialist(name, agent, config_obj.role, config_obj.capabilities)
        
        # Create workflow manager
        wf_manager = WorkflowManager(orchestrator, pool)
        
        # List available workflows
        workflows = wf_manager.list_workflows()
        print(f"✓ Available workflows: {list(workflows.keys())}")
        
        for name, info in workflows.items():
            print(f"  - {name}: {info['description']} ({info['step_count']} steps)")
        
        return True
        
    except Exception as e:
        print(f"✗ Workflow manager test failed: {e}")
        return False


async def test_simple_multiagent_task():
    """Test a simple multi-agent task execution."""
    try:
        from strandsflow.multiagent import (
            Orchestrator, WorkflowType, A2AServerManager, 
            create_predefined_pool
        )
        from strandsflow.core.config import StrandsFlowConfig
        
        print("\n=== Testing Simple Multi-Agent Task ===")
        
        # Create minimal setup
        config = StrandsFlowConfig()
        pool = await create_predefined_pool(config)
        
        # Initialize one specialist for testing
        code_expert = pool.get_specialist("Code Expert")
        if code_expert:
            await code_expert.initialize()
            print("✓ Initialized Code Expert specialist")
            
            # Test direct agent communication
            response = await code_expert.chat("What are the key principles of clean code?")
            print(f"✓ Code Expert response: {response[:100]}...")
            
            await code_expert.shutdown()
            print("✓ Code Expert shutdown complete")
        
        return True
        
    except Exception as e:
        print(f"✗ Simple multi-agent task failed: {e}")
        return False


async def run_all_tests():
    """Run all multi-agent tests."""
    print("🚀 Starting StrandsFlow Multi-Agent Tests")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Specialist Pool Test", test_specialist_pool),
        ("A2A Server Test", test_a2a_server),
        ("Orchestrator Test", test_orchestrator),
        ("Workflow Manager Test", test_workflow_manager),
        ("Simple Multi-Agent Task", test_simple_multiagent_task)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            results.append((test_name, result))
            
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    # Run tests
    asyncio.run(run_all_tests())

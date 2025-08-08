#!/usr/bin/env python3
"""
Integration test for StrandsFlow Sprint 1 deliverables.
"""

import sys
import os

# Set up Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test all core imports."""
    print("🧪 Testing StrandsFlow imports...")
    
    try:
        # Test Strands SDK imports
        from strands import Agent
        from strands.models import BedrockModel
        from strands_tools import calculator, current_time, file_read, file_write, python_repl, shell
        print("✅ Strands SDK imports successful")
        
        # Test core modules
        from strandsflow.core.config import StrandsFlowConfig
        print("✅ StrandsFlow config import successful")
        
        # Test API module
        import strandsflow.api.app
        print("✅ StrandsFlow API module import successful")
        
        # Test CLI module
        import strandsflow.cli
        print("✅ StrandsFlow CLI module import successful")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_basic_agent():
    """Test basic agent creation."""
    print("\n🧪 Testing basic agent creation...")
    
    try:
        from strands import Agent
        from strands.models import BedrockModel
        from strands_tools import calculator, current_time
        
        # Create model
        model = BedrockModel(
            model_id="anthropic.claude-sonnet-4-20250514-v1:0",
            region_name="us-west-2",
            temperature=0.7,
            max_tokens=4096,
        )
        print("✅ BedrockModel created successfully")
        
        # Create agent
        agent = Agent(model=model, tools=[calculator, current_time])
        print("✅ Strands Agent created successfully")
        
        # Check configuration
        config = agent.model.config
        print(f"✅ Model config: {config}")
        
        return True
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        return False


def test_config():
    """Test configuration system."""
    print("\n🧪 Testing configuration...")
    
    try:
        from strandsflow.core.config import StrandsFlowConfig
        
        config = StrandsFlowConfig()
        print(f"✅ Default config created: {config.agent.name}")
        print(f"✅ Model ID: {config.bedrock.model_id}")
        print(f"✅ API port: {config.api.port}")
        print(f"✅ Bedrock region: {config.bedrock.region_name}")
        print(f"✅ Temperature: {config.bedrock.temperature}")
        
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 StrandsFlow Sprint 1 Integration Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_basic_agent,
        test_config,
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("🎉 All Sprint 1 tests passed!")
        print("✅ StrandsFlow is ready for Sprint 2")
    else:
        print("⚠️ Some tests failed")
        print("💡 Note: AWS credential issues are expected without proper setup")
    
    return passed == len(tests)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

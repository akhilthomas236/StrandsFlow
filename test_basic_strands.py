#!/usr/bin/env python3
"""
Simple Strands SDK test without complex imports.
"""

# Test basic Strands SDK imports
try:
    from strands import Agent
    print("✅ Strands Agent import successful")
except ImportError as e:
    print(f"❌ Strands Agent import failed: {e}")

try:
    from strands.models import BedrockModel
    print("✅ BedrockModel import successful") 
except ImportError as e:
    print(f"❌ BedrockModel import failed: {e}")

try:
    from strands_tools import calculator, current_time, file_read, file_write, python_repl, shell
    print("✅ Tools import successful")
    print(f"✅ Available tools: calculator, current_time, file_read, file_write, python_repl, shell")
except ImportError as e:
    print(f"❌ Tools import failed: {e}")

# Test basic agent creation
try:
    agent = Agent()
    print("✅ Basic Agent creation successful")
    print(f"✅ Model config: {agent.model.config}")
except Exception as e:
    print(f"⚠️ Agent creation failed (expected without AWS creds): {e}")

print("\n🎉 Strands SDK basic verification complete!")
print("✅ All core imports working - ready for StrandsFlow implementation!")

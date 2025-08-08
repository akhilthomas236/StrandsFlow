"""Test suite for StrandsFlow configuration management."""

import pytest
from pathlib import Path
import tempfile
import json
import os

from strandsflow.core.config import (
    StrandsFlowConfig,
    BedrockConfig,
    MCPConfig,
    AgentConfig,
    APIConfig,
    DEFAULT_BEDROCK_MODEL_ID,
    DEFAULT_BEDROCK_REGION,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS
)


class TestBedrockConfig:
    """Test BedrockConfig class."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = BedrockConfig()
        
        assert config.model_id == DEFAULT_BEDROCK_MODEL_ID
        assert config.region_name == DEFAULT_BEDROCK_REGION
        assert config.temperature == DEFAULT_TEMPERATURE
        assert config.max_tokens == DEFAULT_MAX_TOKENS
        assert config.streaming is True
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = BedrockConfig(
            model_id="custom-model",
            region_name="eu-west-1",
            temperature=0.5,
            max_tokens=2048,
            streaming=False
        )
        
        assert config.model_id == "custom-model"
        assert config.region_name == "eu-west-1"
        assert config.temperature == 0.5
        assert config.max_tokens == 2048
        assert config.streaming is False
    
    def test_validation(self):
        """Test configuration validation."""
        # Temperature bounds
        with pytest.raises(ValueError):
            BedrockConfig(temperature=-0.1)
        
        with pytest.raises(ValueError):
            BedrockConfig(temperature=1.1)
        
        # Max tokens
        with pytest.raises(ValueError):
            BedrockConfig(max_tokens=0)


class TestMCPConfig:
    """Test MCPConfig class."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = MCPConfig()
        
        assert config.servers == {}
        assert config.auto_discover is True
        assert config.default_transport == "stdio"
        assert config.connection_timeout == 30
        assert len(config.discovery_paths) == 2
    
    def test_custom_servers(self):
        """Test custom server configuration."""
        servers = {
            "calculator": {
                "transport": "stdio",
                "command": "python",
                "args": ["calculator_server.py"]
            }
        }
        
        config = MCPConfig(servers=servers)
        assert config.servers == servers


class TestAgentConfig:
    """Test AgentConfig class."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = AgentConfig()
        
        assert config.name == "StrandsFlow Agent"
        assert "AI agent powered by AWS Bedrock" in config.description
        assert config.max_conversation_turns == 50
        assert config.system_prompt is None
        assert config.enable_memory is True


class TestAPIConfig:
    """Test APIConfig class."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = APIConfig()
        
        assert config.host == "127.0.0.1"
        assert config.port == 8000
        assert config.workers == 1
        assert config.reload is False
        assert config.cors_origins == ["*"]
    
    def test_port_validation(self):
        """Test port validation."""
        with pytest.raises(ValueError):
            APIConfig(port=0)
        
        with pytest.raises(ValueError):
            APIConfig(port=65536)


class TestStrandsFlowConfig:
    """Test main StrandsFlowConfig class."""
    
    def test_default_configuration(self):
        """Test default configuration creation."""
        config = StrandsFlowConfig()
        
        assert isinstance(config.bedrock, BedrockConfig)
        assert isinstance(config.mcp, MCPConfig)
        assert isinstance(config.agent, AgentConfig)
        assert isinstance(config.api, APIConfig)
    
    def test_from_env(self):
        """Test configuration from environment variables."""
        # Set environment variables
        os.environ.update({
            "BEDROCK_MODEL_ID": "test-model",
            "AWS_REGION": "us-east-1",
            "BEDROCK_TEMPERATURE": "0.5",
            "BEDROCK_MAX_TOKENS": "2048",
            "AGENT_NAME": "Test Agent",
            "API_PORT": "9000"
        })
        
        try:
            config = StrandsFlowConfig.from_env()
            
            assert config.bedrock.model_id == "test-model"
            assert config.bedrock.region_name == "us-east-1"
            assert config.bedrock.temperature == 0.5
            assert config.bedrock.max_tokens == 2048
            assert config.agent.name == "Test Agent"
            assert config.api.port == 9000
        finally:
            # Clean up environment variables
            for key in ["BEDROCK_MODEL_ID", "AWS_REGION", "BEDROCK_TEMPERATURE", 
                       "BEDROCK_MAX_TOKENS", "AGENT_NAME", "API_PORT"]:
                os.environ.pop(key, None)
    
    def test_file_operations(self):
        """Test saving and loading configuration files."""
        config = StrandsFlowConfig()
        config.agent.name = "Test Agent"
        config.bedrock.temperature = 0.5
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test JSON file
            json_path = Path(temp_dir) / "config.json"
            config.save_to_file(str(json_path))
            
            assert json_path.exists()
            loaded_config = StrandsFlowConfig.from_file(str(json_path))
            
            assert loaded_config.agent.name == "Test Agent"
            assert loaded_config.bedrock.temperature == 0.5
            
            # Test YAML file
            yaml_path = Path(temp_dir) / "config.yaml"
            config.save_to_file(str(yaml_path))
            
            assert yaml_path.exists()
            loaded_config = StrandsFlowConfig.from_file(str(yaml_path))
            
            assert loaded_config.agent.name == "Test Agent"
            assert loaded_config.bedrock.temperature == 0.5
    
    def test_file_not_found(self):
        """Test loading from non-existent file."""
        with pytest.raises(FileNotFoundError):
            StrandsFlowConfig.from_file("nonexistent.yaml")


if __name__ == "__main__":
    pytest.main([__file__])

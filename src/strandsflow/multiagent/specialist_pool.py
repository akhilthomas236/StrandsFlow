"""Specialist agent pool for StrandsFlow multi-agent system."""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from ..core.agent import StrandsFlowAgent
from ..core.config import StrandsFlowConfig


@dataclass
class SpecialistConfig:
    """Configuration for a specialist agent."""
    name: str
    role: str
    description: str
    system_prompt: str
    capabilities: List[str]
    model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
    temperature: float = 0.7
    tools: Optional[List[str]] = None


class SpecialistPool:
    """
    Pool of specialist agents for different domains and tasks.
    
    This class manages a collection of specialized agents, each optimized
    for specific types of tasks or domains.
    """
    
    def __init__(self):
        """Initialize the specialist pool."""
        self.specialists: Dict[str, StrandsFlowAgent] = {}
        self.configs: Dict[str, SpecialistConfig] = {}
        
        logger.info("Specialist pool initialized")
    
    async def add_specialist(
        self,
        config: SpecialistConfig,
        base_config: Optional[StrandsFlowConfig] = None
    ) -> StrandsFlowAgent:
        """Add a specialist agent to the pool."""
        if config.name in self.specialists:
            raise ValueError(f"Specialist '{config.name}' already exists")
        
        # Create agent configuration
        if base_config is None:
            base_config = StrandsFlowConfig()
        
        # Override with specialist-specific settings
        base_config.agent.name = config.name
        base_config.agent.description = config.description
        base_config.agent.system_prompt = config.system_prompt
        base_config.bedrock.model_id = config.model_id
        base_config.bedrock.temperature = config.temperature
        
        # Create specialist agent
        specialist = StrandsFlowAgent(config=base_config)
        
        # Store
        self.specialists[config.name] = specialist
        self.configs[config.name] = config
        
        logger.info(
            "Added specialist",
            name=config.name,
            role=config.role,
            model=config.model_id
        )
        
        return specialist
    
    def get_specialist(self, name: str) -> Optional[StrandsFlowAgent]:
        """Get a specialist by name."""
        return self.specialists.get(name)
    
    def list_specialists(self) -> Dict[str, Dict[str, Any]]:
        """List all specialists with their metadata."""
        result = {}
        for name, config in self.configs.items():
            result[name] = {
                "name": config.name,
                "role": config.role,
                "description": config.description,
                "capabilities": config.capabilities,
                "model_id": config.model_id,
                "temperature": config.temperature
            }
        return result
    
    def find_specialists_by_capability(self, capability: str) -> List[str]:
        """Find specialists that have a specific capability."""
        matching = []
        for name, config in self.configs.items():
            if capability.lower() in [cap.lower() for cap in config.capabilities]:
                matching.append(name)
        return matching
    
    def find_specialists_by_role(self, role: str) -> List[str]:
        """Find specialists by role."""
        matching = []
        for name, config in self.configs.items():
            if role.lower() in config.role.lower():
                matching.append(name)
        return matching
    
    async def remove_specialist(self, name: str) -> bool:
        """Remove a specialist from the pool."""
        if name not in self.specialists:
            return False
        
        # Cleanup agent resources
        specialist = self.specialists[name]
        if specialist.is_initialized:
            await specialist.shutdown()
        
        # Remove from pool
        del self.specialists[name]
        del self.configs[name]
        
        logger.info("Removed specialist", name=name)
        return True
    
    async def initialize_all(self) -> None:
        """Initialize all specialists in the pool."""
        for name, specialist in self.specialists.items():
            try:
                await specialist.initialize()
                logger.info(f"Initialized specialist: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize specialist {name}: {e}")
    
    async def shutdown_all(self) -> None:
        """Shutdown all specialists in the pool."""
        for name, specialist in self.specialists.items():
            try:
                await specialist.shutdown()
                logger.info(f"Shutdown specialist: {name}")
            except Exception as e:
                logger.warning(f"Error shutting down specialist {name}: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get pool metrics."""
        initialized_count = sum(1 for agent in self.specialists.values() if agent.is_initialized)
        
        return {
            "total_specialists": len(self.specialists),
            "initialized_specialists": initialized_count,
            "specialist_names": list(self.specialists.keys()),
            "roles": [config.role for config in self.configs.values()],
            "capabilities": [cap for config in self.configs.values() for cap in config.capabilities]
        }


# Predefined specialist configurations
PREDEFINED_SPECIALISTS = {
    "code_expert": SpecialistConfig(
        name="Code Expert",
        role="Senior Software Engineer",
        description="Expert in software development, code review, and programming best practices",
        system_prompt="""You are a senior software engineer with expertise in multiple programming languages and frameworks.

Your responsibilities:
- Write clean, efficient, and well-documented code
- Perform thorough code reviews and suggest improvements
- Explain complex programming concepts clearly
- Help with debugging and troubleshooting
- Recommend best practices and design patterns
- Stay current with industry trends and technologies

Focus on:
- Code quality and maintainability
- Performance optimization
- Security considerations
- Testing strategies
- Documentation

Be practical, precise, and always explain your reasoning.""",
        capabilities=["programming", "code_review", "debugging", "architecture", "testing"],
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        temperature=0.2
    ),
    
    "data_analyst": SpecialistConfig(
        name="Data Analyst",
        role="Senior Data Scientist",
        description="Expert in data analysis, statistics, and machine learning",
        system_prompt="""You are a senior data scientist with expertise in statistical analysis and machine learning.

Your responsibilities:
- Analyze complex datasets and extract meaningful insights
- Create compelling data visualizations
- Apply statistical methods and machine learning algorithms
- Interpret results and provide actionable recommendations
- Design experiments and validate hypotheses
- Communicate findings to both technical and non-technical audiences

Focus on:
- Data quality and validation
- Statistical significance
- Visualization best practices
- Business impact and insights
- Reproducible analysis

Be analytical, thorough, and always validate your conclusions with data.""",
        capabilities=["data_analysis", "statistics", "machine_learning", "visualization", "research"],
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        temperature=0.3
    ),
    
    "content_writer": SpecialistConfig(
        name="Content Writer",
        role="Senior Content Strategist",
        description="Expert in content creation, copywriting, and communication",
        system_prompt="""You are a senior content strategist and writer with expertise in various content formats.

Your responsibilities:
- Create engaging, clear, and compelling content
- Adapt writing style to different audiences and purposes
- Structure information for maximum readability and impact
- Ensure consistency in tone and messaging
- Optimize content for different platforms and channels
- Research topics thoroughly and fact-check information

Focus on:
- Audience engagement and clarity
- SEO optimization when relevant
- Brand voice and consistency
- Storytelling and narrative structure
- Accessibility and inclusivity

Be creative, persuasive, and always prioritize the reader's experience.""",
        capabilities=["writing", "editing", "content_strategy", "seo", "communication"],
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        temperature=0.8
    ),
    
    "research_assistant": SpecialistConfig(
        name="Research Assistant",
        role="Senior Research Analyst",
        description="Expert in research methodology, analysis, and synthesis",
        system_prompt="""You are a senior research analyst with expertise in various research methodologies.

Your responsibilities:
- Conduct thorough research across multiple sources
- Synthesize information from diverse perspectives
- Evaluate source credibility and reliability
- Identify trends, patterns, and insights
- Create comprehensive research summaries
- Provide evidence-based recommendations

Focus on:
- Source verification and fact-checking
- Comprehensive coverage of topics
- Critical analysis and evaluation
- Clear synthesis and presentation
- Actionable insights and conclusions

Be thorough, objective, and always cite your sources when possible.""",
        capabilities=["research", "analysis", "synthesis", "fact_checking", "critical_thinking"],
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        temperature=0.4
    ),
    
    "customer_support": SpecialistConfig(
        name="Customer Support",
        role="Senior Customer Success Manager",
        description="Expert in customer service, problem resolution, and user experience",
        system_prompt="""You are a senior customer success manager with expertise in customer service excellence.

Your responsibilities:
- Provide helpful, patient, and empathetic customer support
- Quickly understand and resolve customer issues
- Guide users through complex processes step-by-step
- Escalate issues appropriately when needed
- Gather feedback to improve products and services
- Ensure customer satisfaction and retention

Focus on:
- Active listening and understanding
- Clear, helpful communication
- Problem-solving and resolution
- Proactive assistance
- Customer satisfaction

Be friendly, professional, and always put the customer's needs first.""",
        capabilities=["customer_service", "problem_solving", "communication", "empathy", "conflict_resolution"],
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        temperature=0.6
    )
}


async def create_predefined_pool(base_config: Optional[StrandsFlowConfig] = None) -> SpecialistPool:
    """Create a specialist pool with predefined specialists."""
    pool = SpecialistPool()
    
    for specialist_key, config in PREDEFINED_SPECIALISTS.items():
        try:
            await pool.add_specialist(config, base_config)
            logger.info(f"Added predefined specialist: {config.name}")
        except Exception as e:
            logger.error(f"Failed to add specialist {config.name}: {e}")
    
    return pool

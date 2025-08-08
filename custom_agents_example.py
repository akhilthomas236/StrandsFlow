"""
Custom Agent Implementation Example
"""

import asyncio
from typing import Dict, List, Optional, Any
from strandsflow.core.agent import StrandsFlowAgent
from strandsflow.core.config import StrandsFlowConfig


class DataAnalysisAgent(StrandsFlowAgent):
    """
    Custom agent specialized for data analysis tasks.
    """
    
    def __init__(self, config: Optional[StrandsFlowConfig] = None):
        # Custom system prompt for data analysis
        custom_system_prompt = """
        You are DataBot, an expert data analyst and visualization specialist.
        
        Your capabilities:
        - Statistical analysis and hypothesis testing
        - Data cleaning and preprocessing
        - Creating charts, graphs, and visualizations
        - Business intelligence and reporting
        - Machine learning model interpretation
        
        Always:
        1. Ask clarifying questions about data context
        2. Explain your analytical approach
        3. Provide actionable insights
        4. Suggest next steps for deeper analysis
        
        Available tools: calculator, file operations, Python REPL for analysis
        """
        
        super().__init__(
            config=config,
            system_prompt=custom_system_prompt
        )
        
        # Add custom initialization
        self.analysis_history = []
        self.data_cache = {}
    
    async def analyze_data(self, data_path: str, analysis_type: str = "descriptive") -> Dict[str, Any]:
        """
        Perform specialized data analysis.
        
        Args:
            data_path: Path to data file
            analysis_type: Type of analysis (descriptive, inferential, predictive)
            
        Returns:
            Analysis results dictionary
        """
        try:
            # Custom data analysis logic
            prompt = f"""
            I need to perform {analysis_type} analysis on data from {data_path}.
            
            Please:
            1. Load and examine the data structure
            2. Perform {analysis_type} analysis
            3. Identify key insights and patterns
            4. Suggest visualization recommendations
            5. Provide summary and next steps
            
            Use the available tools to access and analyze the data.
            """
            
            result = await self.chat(prompt)
            
            # Store analysis in history
            analysis_record = {
                "data_path": data_path,
                "analysis_type": analysis_type,
                "result": result,
                "timestamp": "2025-08-08T00:00:00Z"
            }
            self.analysis_history.append(analysis_record)
            
            return {
                "success": True,
                "analysis": result,
                "record_id": len(self.analysis_history) - 1
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "analysis": None
            }
    
    async def generate_report(self, analysis_ids: List[int]) -> str:
        """
        Generate a comprehensive report from multiple analyses.
        
        Args:
            analysis_ids: List of analysis record IDs to include
            
        Returns:
            Generated report as markdown string
        """
        try:
            # Gather selected analyses
            selected_analyses = [
                self.analysis_history[i] for i in analysis_ids 
                if i < len(self.analysis_history)
            ]
            
            # Create report prompt
            analyses_summary = "\n\n".join([
                f"Analysis {i}: {analysis['analysis_type']} on {analysis['data_path']}\n"
                f"Results: {analysis['result'][:500]}..."
                for i, analysis in enumerate(selected_analyses)
            ])
            
            prompt = f"""
            Create a comprehensive data analysis report based on these analyses:
            
            {analyses_summary}
            
            Please create a professional report with:
            1. Executive Summary
            2. Methodology
            3. Key Findings
            4. Visualizations Recommendations
            5. Conclusions and Recommendations
            6. Next Steps
            
            Format as markdown for easy reading.
            """
            
            report = await self.chat(prompt)
            return report
            
        except Exception as e:
            return f"Error generating report: {str(e)}"
    
    def get_analysis_history(self) -> List[Dict[str, Any]]:
        """Get the history of all analyses performed."""
        return self.analysis_history.copy()
    
    async def custom_chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Enhanced chat with custom context handling.
        
        Args:
            message: User message
            context: Additional context (data paths, previous analyses, etc.)
            
        Returns:
            Agent response
        """
        # Add context to the message if provided
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            enhanced_message = f"""
            Context:
            {context_str}
            
            User Query: {message}
            
            Please consider the provided context when responding.
            """
        else:
            enhanced_message = message
        
        return await self.chat(enhanced_message)


class CodeReviewAgent(StrandsFlowAgent):
    """
    Custom agent specialized for code review and analysis.
    """
    
    def __init__(self, config: Optional[StrandsFlowConfig] = None):
        custom_system_prompt = """
        You are CodeReviewer, an expert software engineer specializing in code quality and security.
        
        Your expertise:
        - Code quality assessment
        - Security vulnerability detection
        - Performance optimization suggestions
        - Best practices enforcement
        - Documentation review
        
        For each code review:
        1. Analyze code structure and logic
        2. Identify potential issues and bugs
        3. Suggest improvements
        4. Rate code quality (1-10)
        5. Provide specific, actionable feedback
        """
        
        super().__init__(
            config=config,
            system_prompt=custom_system_prompt
        )
        
        self.review_history = []
    
    async def review_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Perform comprehensive code review.
        
        Args:
            code: Code to review
            language: Programming language
            
        Returns:
            Review results
        """
        prompt = f"""
        Please review this {language} code:
        
        ```{language}
        {code}
        ```
        
        Provide a detailed review covering:
        1. Code quality and readability
        2. Security vulnerabilities
        3. Performance considerations
        4. Best practices compliance
        5. Suggested improvements
        6. Overall rating (1-10)
        """
        
        review = await self.chat(prompt)
        
        # Store review
        review_record = {
            "code": code[:200] + "..." if len(code) > 200 else code,
            "language": language,
            "review": review,
            "timestamp": "2025-08-08T00:00:00Z"
        }
        self.review_history.append(review_record)
        
        return {
            "success": True,
            "review": review,
            "record_id": len(self.review_history) - 1
        }


# Factory function for creating custom agents
def create_custom_agent(agent_type: str, config_path: str = None) -> StrandsFlowAgent:
    """
    Factory function to create different types of custom agents.
    
    Args:
        agent_type: Type of agent to create
        config_path: Path to custom configuration file
        
    Returns:
        Custom agent instance
    """
    # Load custom config if provided
    if config_path:
        config = StrandsFlowConfig.from_file(config_path)
    else:
        config = StrandsFlowConfig()
    
    # Create appropriate agent type
    if agent_type == "data_analysis":
        return DataAnalysisAgent(config)
    elif agent_type == "code_review":
        return CodeReviewAgent(config)
    else:
        # Default StrandsFlow agent with custom config
        return StrandsFlowAgent(config)


# Example usage
async def main():
    """Example of using custom agents."""
    
    # Create a data analysis agent
    data_agent = create_custom_agent("data_analysis", "custom_agent_config.yaml")
    await data_agent.initialize()
    
    # Perform data analysis
    result = await data_agent.analyze_data(
        data_path="/path/to/sales_data.csv",
        analysis_type="descriptive"
    )
    
    print("Analysis Result:", result)
    
    # Create a code review agent
    code_agent = create_custom_agent("code_review")
    await code_agent.initialize()
    
    # Review some code
    sample_code = """
    def calculate_total(items):
        total = 0
        for item in items:
            total += item['price']
        return total
    """
    
    review = await code_agent.review_code(sample_code, "python")
    print("Code Review:", review)
    
    # Cleanup
    await data_agent.shutdown()
    await code_agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

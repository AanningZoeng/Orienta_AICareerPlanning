"""
Future Path Agent - Projects career progression and future development paths.
"""
import asyncio
from typing import Dict, Any, List
from spoon_ai.agents.toolcall import ToolCallAgent
from spoon_ai.chat import ChatBot
from spoon_ai.tools import ToolManager
from backend.tools.linkedin_analyzer_tool import LinkedInAnalyzerTool


class FuturePathAgent(ToolCallAgent):
    """Agent specialized in analyzing future career progression patterns."""
    
    name: str = "future_path_agent"
    description: str = "Projects future career development paths using professional network data and industry trends"
    system_prompt: str = """
    You are a career progression analyst. Your role is to:
    1. Analyze career progression patterns from professional networks
    2. Calculate statistics on promotions, job changes, and career transitions
    3. Identify common future paths for professionals in each career
    4. Provide data-driven insights about career development
    
    Use LinkedIn-style data to understand how professionals progress over 5-10 years.
    Provide realistic statistics and multiple possible progression paths.
    Consider both vertical advancement and lateral moves.
    
    Return data in structured JSON format with clear statistics and progression paths.
    """
    available_tools: ToolManager = ToolManager([LinkedInAnalyzerTool()])
    
    async def analyze_progression(self, career_title: str, years: int = 5) -> Dict[str, Any]:
        """
        Analyze career progression for a specific role.
        
        Args:
            career_title: Title of the career to analyze
            years: Number of years to project (default: 5)
            
        Returns:
            Progression statistics and common paths
        """
        # Use LinkedIn analyzer tool
        linkedin_tool = LinkedInAnalyzerTool()
        progression_data = await linkedin_tool.execute(
            career_title=career_title,
            years_experience=years
        )
        
        if progression_data.get("success"):
            stats = progression_data["statistics"]
            
            # Build future path structure
            return {
                "id": f"{career_title.lower().replace(' ', '_')}_future",
                "career": career_title,
                "timeframe": progression_data["timeframe"],
                "statistics": {
                    "promoted": {
                        "percentage": stats["promoted"],
                        "description": f"{stats['promoted']}% of professionals were promoted to higher positions"
                    },
                    "same_role": {
                        "percentage": stats["same_role"],
                        "description": f"{stats['same_role']}% continued in similar roles with skill development"
                    },
                    "changed_company": {
                        "percentage": stats["changed_company"],
                        "description": f"{stats['changed_company']}% moved to different companies for better opportunities"
                    },
                    "changed_career": {
                        "percentage": stats["changed_career"],
                        "description": f"{stats['changed_career']}% transitioned to different career paths"
                    },
                    "laid_off": {
                        "percentage": stats["laid_off"],
                        "description": f"{stats['laid_off']}% experienced layoffs or job loss"
                    }
                },
                "common_progressions": stats["common_progressions"],
                "salary_growth": stats["average_salary_growth"],
                "job_satisfaction": stats["job_satisfaction"],
                "sample_size": progression_data["sample_size"],
                "insights": self._generate_insights(stats)
            }
        
        return {}
    
    def _generate_insights(self, stats: Dict[str, Any]) -> List[str]:
        """Generate actionable insights from statistics."""
        insights = []
        
        if stats["promoted"] > 40:
            insights.append("🎯 Strong promotion rate - excellent growth opportunities")
        
        if stats["changed_company"] > 10:
            insights.append("🔄 Active job market - professionals frequently move for better opportunities")
        
        if stats["laid_off"] < 5:
            insights.append("✅ High job security - low layoff rate indicates stable career")
        
        if "15%" in str(stats.get("average_salary_growth", "")) or "18%" in str(stats.get("average_salary_growth", "")):
            insights.append("💰 Above-average salary growth potential")
        
        if int(stats.get("job_satisfaction", "0%").rstrip("%")) > 70:
            insights.append("😊 High job satisfaction reported by professionals")
        
        return insights
    
    async def process_careers(self, careers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze future paths for multiple careers.
        
        Args:
            careers: List of career dictionaries with at least 'title' field
            
        Returns:
            List of future path analyses
        """
        future_paths = []
        
        for career in careers:
            career_title = career.get("title", career.get("name", ""))
            if career_title:
                path_data = await self.analyze_progression(career_title)
                if path_data:
                    future_paths.append(path_data)
        
        return future_paths


# Factory function
def create_future_path_agent(llm_provider: str = "openai", model_name: str = "gpt-4o") -> FuturePathAgent:
    """Create a FuturePathAgent with specified LLM configuration."""
    return FuturePathAgent(
        llm=ChatBot(
            llm_provider=llm_provider,
            model_name=model_name
        )
    )

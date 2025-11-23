"""
Career Analysis Agent - Analyzes careers related to university majors.
"""
import asyncio
from typing import Dict, Any, List
from spoon_ai.agents.toolcall import ToolCallAgent
from spoon_ai.chat import ChatBot
from spoon_ai.tools import ToolManager
from backend.tools.media_finder_tool import MediaFinderTool


class CareerAnalysisAgent(ToolCallAgent):
    """Agent specialized in analyzing career paths for university majors."""
    
    name: str = "career_analysis_agent"
    description: str = "Analyzes career opportunities, salaries, and professional resources for different majors"
    system_prompt: str = """
    You are a career analysis expert. Your role is to:
    1. Identify career paths associated with specific university majors
    2. Research salary ranges, benefits, and work conditions
    3. Find professional resources (YouTube channels, blogs, interviews)
    4. Provide realistic career expectations
    
    For each major, identify 3-4 distinct career paths that graduates commonly pursue.
    Consider various career trajectories: corporate roles, startups, research, consulting, etc.
    
    Provide detailed, honest information about each career including pros and cons.
    Return data in structured JSON format.
    """
    available_tools: ToolManager = ToolManager([MediaFinderTool()])
    
    async def identify_careers(self, major_name: str) -> List[str]:
        """
        Identify career paths for a given major.
        
        Args:
            major_name: Name of the university major
            
        Returns:
            List of career titles
        """
        # Predefined career mappings for common majors
        career_mappings = {
            "Computer Science": ["Software Engineer", "Data Scientist", "DevOps Engineer", "Product Manager"],
            "Business Administration": ["Marketing Manager", "Financial Analyst", "Management Consultant", "Operations Manager"],
            "Psychology": ["Clinical Psychologist", "HR Manager", "UX Researcher", "Counselor"],
            "Mechanical Engineering": ["Mechanical Engineer", "Robotics Engineer", "Manufacturing Engineer", "Project Manager"]
        }
        
        # Return predefined careers or generate generic ones
        if major_name in career_mappings:
            return career_mappings[major_name]
        else:
            return [f"{major_name} Specialist", f"Senior {major_name} Professional", f"{major_name} Manager"]
    
    async def analyze_career(self, career_title: str) -> Dict[str, Any]:
        """
        Analyze a specific career in detail.
        
        Args:
            career_title: Title of the career to analyze
            
        Returns:
            Detailed career information
        """
        # Career salary and work condition database (mock data)
        career_database = {
            "Software Engineer": {
                "salary_range": "$80,000 - $180,000",
                "average_salary": "$120,000",
                "benefits": ["Health insurance", "401(k) matching", "Stock options", "Remote work options"],
                "work_intensity": "Medium to High",
                "work_life_balance": "Good (flexible hours, remote options)",
                "growth_potential": "Excellent",
                "job_outlook": "Growing rapidly (+22% by 2030)"
            },
            "Marketing Manager": {
                "salary_range": "$60,000 - $140,000",
                "average_salary": "$95,000",
                "benefits": ["Health insurance", "Performance bonuses", "Professional development", "Flexible schedule"],
                "work_intensity": "Medium",
                "work_life_balance": "Good",
                "growth_potential": "Very Good",
                "job_outlook": "Growing (+10% by 2030)"
            },
            "Data Scientist": {
                "salary_range": "$90,000 - $200,000",
                "average_salary": "$130,000",
                "benefits": ["Comprehensive health", "Stock options", "Learning budget", "Remote work"],
                "work_intensity": "Medium to High",
                "work_life_balance": "Good",
                "growth_potential": "Excellent",
                "job_outlook": "Very Strong (+36% by 2030)"
            },
            "Financial Analyst": {
                "salary_range": "$55,000 - $120,000",
                "average_salary": "$85,000",
                "benefits": ["Health insurance", "Bonuses", "Retirement plans", "CFA sponsorship"],
                "work_intensity": "High",
                "work_life_balance": "Moderate (long hours during quarter-end)",
                "growth_potential": "Good",
                "job_outlook": "Stable (+5% by 2030)"
            }
        }
        
        # Get career data or create generic one
        if career_title in career_database:
            career_data = career_database[career_title]
        else:
            career_data = {
                "salary_range": "$50,000 - $100,000",
                "average_salary": "$75,000",
                "benefits": ["Health insurance", "Paid time off", "Professional development"],
                "work_intensity": "Medium",
                "work_life_balance": "Good",
                "growth_potential": "Good",
                "job_outlook": "Stable"
            }
        
        # Get professional media resources
        media_finder = MediaFinderTool()
        media_resources = await media_finder.execute(career_or_major=career_title, content_type="all")
        
        return {
            "id": career_title.lower().replace(" ", "_"),
            "title": career_title,
            **career_data,
            "professional_resources": media_resources.get("content", {})
        }
    
    async def process_major(self, major_name: str) -> Dict[str, Any]:
        """
        Analyze all careers for a given major.
        
        Args:
            major_name: Name of the university major
            
        Returns:
            Structured data with career details
        """
        # Step 1: Identify careers for this major
        career_titles = await self.identify_careers(major_name)
        
        # Step 2: Analyze each career in detail
        career_analyses = []
        for career_title in career_titles:
            career_data = await self.analyze_career(career_title)
            career_analyses.append(career_data)
        
        return {
            "major": major_name,
            "careers": career_analyses,
            "count": len(career_analyses)
        }


# Factory function
def create_career_analysis_agent(llm_provider: str = "openai", model_name: str = "gpt-4o") -> CareerAnalysisAgent:
    """Create a CareerAnalysisAgent with specified LLM configuration."""
    return CareerAnalysisAgent(
        llm=ChatBot(
            llm_provider=llm_provider,
            model_name=model_name
        )
    )

"""
LinkedIn analyzer tool for career progression data.
Simulates LinkedIn data analysis with realistic statistics.
"""
from typing import Any, Dict
from spoon_ai.tools.base import BaseTool
import random


class LinkedInAnalyzerTool(BaseTool):
    """Tool for analyzing career progression patterns from professional networks."""
    
    name: str = "linkedin_analyzer"
    description: str = "Analyzes career progression data to provide statistics on promotions, layoffs, and career transitions"
    parameters: dict = {
        "type": "object",
        "properties": {
            "career_title": {
                "type": "string",
                "description": "Job title or career path to analyze"
            },
            "years_experience": {
                "type": "integer",
                "description": "Years of experience to analyze progression for (default: 5)"
            }
        },
        "required": ["career_title"]
    }
    
    async def execute(self, career_title: str, years_experience: int = 5) -> Dict[str, Any]:
        """
        Simulate LinkedIn career progression analysis.
        
        In production, this would use LinkedIn API or web scraping.
        For demo, we return realistic statistical data.
        """
        # Mock career progression patterns
        career_patterns = {
            "Software Engineer": {
                "promoted": 45,
                "same_role": 30,
                "changed_company": 15,
                "changed_career": 5,
                "laid_off": 5,
                "common_progressions": [
                    "Senior Software Engineer (35%)",
                    "Tech Lead (20%)",
                    "Engineering Manager (15%)",
                    "Product Manager (10%)",
                    "Startup Founder (5%)"
                ],
                "average_salary_growth": "15% per year",
                "job_satisfaction": "73%"
            },
            "Marketing Manager": {
                "promoted": 40,
                "same_role": 35,
                "changed_company": 12,
                "changed_career": 8,
                "laid_off": 5,
                "common_progressions": [
                    "Senior Marketing Manager (30%)",
                    "Director of Marketing (25%)",
                    "VP Marketing (10%)",
                    "CMO (5%)",
                    "Consultant (8%)"
                ],
                "average_salary_growth": "12% per year",
                "job_satisfaction": "68%"
            },
            "Data Analyst": {
                "promoted": 50,
                "same_role": 25,
                "changed_company": 15,
                "changed_career": 7,
                "laid_off": 3,
                "common_progressions": [
                    "Senior Data Analyst (35%)",
                    "Data Scientist (30%)",
                    "Analytics Manager (15%)",
                    "Business Intelligence Lead (10%)",
                    "Product Analyst (5%)"
                ],
                "average_salary_growth": "18% per year",
                "job_satisfaction": "75%"
            },
            "Financial Analyst": {
                "promoted": 42,
                "same_role": 33,
                "changed_company": 14,
                "changed_career": 6,
                "laid_off": 5,
                "common_progressions": [
                    "Senior Financial Analyst (35%)",
                    "Finance Manager (25%)",
                    "Investment Banker (12%)",
                    "CFO (5%)",
                    "Portfolio Manager (8%)"
                ],
                "average_salary_growth": "14% per year",
                "job_satisfaction": "70%"
            }
        }
        
        # Get or generate career pattern
        if career_title in career_patterns:
            pattern = career_patterns[career_title]
        else:
            # Generate generic pattern
            pattern = {
                "promoted": random.randint(35, 50),
                "same_role": random.randint(25, 35),
                "changed_company": random.randint(10, 20),
                "changed_career": random.randint(5, 10),
                "laid_off": random.randint(3, 7),
                "common_progressions": [
                    f"Senior {career_title} (30%)",
                    f"{career_title} Manager (25%)",
                    f"Lead {career_title} (20%)"
                ],
                "average_salary_growth": "12-15% per year",
                "job_satisfaction": f"{random.randint(65, 80)}%"
            }
        
        return {
            "success": True,
            "career": career_title,
            "timeframe": f"{years_experience} years",
            "statistics": pattern,
            "sample_size": "10,000+ professionals analyzed",
            "data_source": "Simulated LinkedIn data"
        }

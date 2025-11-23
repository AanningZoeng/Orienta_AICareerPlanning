"""
Web scraper tool for fetching university major information.
Simulates web scraping with realistic mock data for demonstration.
"""
from typing import Any, Dict
from spoon_ai.tools.base import BaseTool


class WebScraperTool(BaseTool):
    """Tool for scraping university websites for major information."""
    
    name: str = "web_scraper"
    description: str = "Scrapes university websites to gather information about academic majors"
    parameters: dict = {
        "type": "object",
        "properties": {
            "major_name": {
                "type": "string",
                "description": "Name of the academic major to research"
            },
            "university": {
                "type": "string",
                "description": "Optional university name to target specific institution"
            }
        },
        "required": ["major_name"]
    }
    
    async def execute(self, major_name: str, university: str = "Various Universities") -> Dict[str, Any]:
        """
        Simulate scraping university websites for major information.
        
        In production, this would make actual HTTP requests to university websites.
        For this demo, we return realistic mock data.
        """
        # Mock data simulating scraped content
        mock_data = {
            "Computer Science": {
                "description": "Computer Science is the study of computers and computational systems. This major covers algorithms, data structures, software engineering, artificial intelligence, machine learning, cybersecurity, and more. Students learn both theoretical foundations and practical programming skills.",
                "requirements": ["Mathematics", "Physics", "Programming Fundamentals", "Data Structures"],
                "duration": "4 years",
                "universities": [
                    {"name": "MIT", "url": "https://www.mit.edu/academics/computer-science"},
                    {"name": "Stanford", "url": "https://cs.stanford.edu"},
                    {"name": "Carnegie Mellon", "url": "https://www.cs.cmu.edu"}
                ],
                "video_url": "https://www.youtube.com/watch?v=example_cs"
            },
            "Business Administration": {
                "description": "Business Administration prepares students for leadership roles in organizations. The curriculum includes finance, marketing, operations management, strategic planning, and organizational behavior. Students develop analytical, communication, and decision-making skills.",
                "requirements": ["Economics", "Statistics", "Accounting", "Management Principles"],
                "duration": "4 years",
                "universities": [
                    {"name": "Harvard Business School", "url": "https://www.hbs.edu"},
                    {"name": "Wharton School", "url": "https://www.wharton.upenn.edu"},
                    {"name": "INSEAD", "url": "https://www.insead.edu"}
                ],
                "video_url": "https://www.youtube.com/watch?v=example_business"
            },
            "Mechanical Engineering": {
                "description": "Mechanical Engineering focuses on the design, analysis, and manufacturing of mechanical systems. Students study thermodynamics, fluid mechanics, materials science, robotics, and CAD design. The major prepares graduates for careers in automotive, aerospace, energy, and manufacturing industries.",
                "requirements": ["Advanced Mathematics", "Physics", "Materials Science", "Engineering Design"],
                "duration": "4 years",
                "universities": [
                    {"name": "Georgia Tech", "url": "https://www.me.gatech.edu"},
                    {"name": "UC Berkeley", "url": "https://me.berkeley.edu"},
                    {"name": "Purdue", "url": "https://engineering.purdue.edu/ME"}
                ],
                "video_url": "https://www.youtube.com/watch?v=example_mech"
            },
            "Psychology": {
                "description": "Psychology is the scientific study of mind and behavior. Students explore cognitive processes, developmental psychology, social psychology, neuroscience, and clinical applications. The major prepares graduates for careers in counseling, research, human resources, and healthcare.",
                "requirements": ["Statistics", "Research Methods", "Biology", "Social Sciences"],
                "duration": "4 years",
                "universities": [
                    {"name": "Yale", "url": "https://psychology.yale.edu"},
                    {"name": "UCLA", "url": "https://www.psych.ucla.edu"},
                    {"name": "University of Michigan", "url": "https://lsa.umich.edu/psych"}
                ],
                "video_url": "https://www.youtube.com/watch?v=example_psych"
            }
        }
        
        # Return mock data for the requested major
        if major_name in mock_data:
            return {
                "success": True,
                "major": major_name,
                "data": mock_data[major_name]
            }
        else:
            # Generate generic data for unknown majors
            return {
                "success": True,
                "major": major_name,
                "data": {
                    "description": f"{major_name} is a comprehensive academic program that prepares students for professional careers in this field. Students gain both theoretical knowledge and practical skills.",
                    "requirements": ["Core Foundation Courses", "Advanced Electives", "Capstone Project"],
                    "duration": "4 years",
                    "universities": [
                        {"name": "Top University", "url": "https://www.university.edu"}
                    ],
                    "video_url": "https://www.youtube.com/watch?v=example"
                }
            }

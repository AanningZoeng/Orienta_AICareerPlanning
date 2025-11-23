"""
Major Research Agent - Researches university majors and academic programs.
"""
import asyncio
from typing import Dict, Any, List
from spoon_ai.agents.toolcall import ToolCallAgent
from spoon_ai.chat import ChatBot
from spoon_ai.tools import ToolManager
from backend.tools.web_scraper_tool import WebScraperTool


class MajorResearchAgent(ToolCallAgent):
    """Agent specialized in researching university majors and academic programs."""
    
    name: str = "major_research_agent"
    description: str = "Researches and analyzes university majors based on user interests and goals"
    system_prompt: str = """
    You are a university major research specialist. Your role is to:
    1. Analyze user interests, skills, and career goals
    2. Identify 3-5 relevant university majors that align with their profile
    3. Gather comprehensive information about each major
    4. Present information in a clear, structured format
    
    When analyzing user input, consider:
    - Their stated interests and passions
    - Skills they mention or imply
    - Career aspirations
    - Work-life balance preferences
    - Industry trends
    
    Always provide diverse options across different fields when appropriate.
    Return your recommendations in a structured JSON format with major names and key details.
    """
    available_tools: ToolManager = ToolManager([WebScraperTool()])
    
    async def analyze_user_interests(self, user_query: str) -> List[str]:
        """
        Analyze user interests and recommend relevant majors.
        
        Args:
            user_query: User's description of interests and goals
            
        Returns:
            List of recommended major names
        """
        # Use LLM to analyze and recommend majors
        prompt = f"""Based on this user query, recommend 3-5 relevant university majors:
        
User Query: "{user_query}"

Recommend majors that align with their interests. Return ONLY a Python list of major names, like:
["Computer Science", "Business Administration", "Psychology"]

Major names:"""
        
        response = await self.run(prompt)
        
        # Parse the response to extract major names
        # For simplicity, we'll use common majors as fallback
        try:
            # Try to extract list from response
            import re
            match = re.search(r'\[(.*?)\]', str(response))
            if match:
                majors_str = match.group(1)
                majors = [m.strip().strip('"').strip("'") for m in majors_str.split(',')]
                return majors[:5]
        except:
            pass
        
        # Fallback to default recommendations
        return ["Computer Science", "Business Administration", "Psychology", "Mechanical Engineering"]
    
    async def research_majors(self, major_names: List[str]) -> List[Dict[str, Any]]:
        """
        Research detailed information about each major.
        
        Args:
            major_names: List of major names to research
            
        Returns:
            List of major details including descriptions, requirements, and universities
        """
        results = []
        scraper = WebScraperTool()
        
        for major_name in major_names:
            # Use the web scraper tool to get major information
            major_data = await scraper.execute(major_name=major_name)
            
            if major_data.get("success"):
                results.append({
                    "id": major_name.lower().replace(" ", "_"),
                    "name": major_name,
                    "description": major_data["data"]["description"],
                    "requirements": major_data["data"]["requirements"],
                    "duration": major_data["data"]["duration"],
                    "universities": major_data["data"]["universities"],
                    "video_url": major_data["data"]["video_url"]
                })
        
        return results
    
    async def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Main entry point: analyze query and research majors.
        
        Args:
            user_query: User's interests and career goals
            
        Returns:
            Structured data with recommended majors and details
        """
        # Step 1: Analyze interests and get major recommendations
        major_names = await self.analyze_user_interests(user_query)
        
        # Step 2: Research each major in detail
        major_details = await self.research_majors(major_names)
        
        return {
            "user_query": user_query,
            "recommended_majors": major_details,
            "count": len(major_details)
        }


# Factory function for easy instantiation
def create_major_research_agent(llm_provider: str = "openai", model_name: str = "gpt-4o") -> MajorResearchAgent:
    """Create a MajorResearchAgent with specified LLM configuration."""
    return MajorResearchAgent(
        llm=ChatBot(
            llm_provider=llm_provider,
            model_name=model_name
        )
    )

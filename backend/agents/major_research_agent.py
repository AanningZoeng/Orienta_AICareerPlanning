"""Major Research Agent - Researches university majors and academic programs.
Now implemented using SpoonReactAI (ReAct style) for LLM calls.
"""
import asyncio
import os
from typing import Dict, Any, List
from spoon_ai.chat import ChatBot
try:
    from spoon_ai.agents import SpoonReactAI
except Exception:
    SpoonReactAI = None
from backend.tools.web_scraper_tool import WebScraperTool
from backend.utils.search_utils import safe_ddg
from backend.utils.llm_utils import TokenEnforcingChatBot
from backend.config import Config
import asyncio


class MajorResearchAgent:
    """Agent specialized in researching university majors and academic programs.

    Uses a ReAct-style `SpoonReactAI` instance (if available) for LLM reasoning.
    """
    
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
    def __init__(self, llm_agent: object = None):
        # llm_agent should be a SpoonReactAI instance (provides async .run(prompt))
        if llm_agent is not None:
            self.llm_agent = llm_agent
        else:
            # Create a default SpoonReactAI if available, otherwise None
            if SpoonReactAI is not None:
                safe_tokens = Config.get_safe_max_tokens(Config.LLM_PROVIDER)
                try:
                    llm = ChatBot(llm_provider=Config.LLM_PROVIDER, model_name=Config.MODEL_NAME, max_tokens=safe_tokens)
                except TypeError:
                    llm = ChatBot(llm_provider=Config.LLM_PROVIDER, model_name=Config.MODEL_NAME)
                self.llm_agent = SpoonReactAI(
                    llm=llm
                )
            else:
                self.llm_agent = None

        # Tools (mock implementations) used directly by the agent logic
        self.scraper = WebScraperTool()
    
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
        
        # Use ReAct agent if available (skip for deepseek to avoid provider errors)
        response = None
        if self.llm_agent is not None and Config.LLM_PROVIDER != "deepseek":
            try:
                response = await self.llm_agent.run(prompt)
            except Exception:
                response = None

        # Parse the response to extract major names
        try:
            import re, json
            match = re.search(r'\[.*\]', str(response), flags=re.S)
            if match:
                items = json.loads(match.group(0))
                if isinstance(items, list) and items:
                    return [str(x).strip() for x in items][:5]
        except Exception:
            pass

        # Fallback: infer majors using DuckDuckGo search (look for program pages and lists)
        majors = []
        try:
            loop = asyncio.get_event_loop()
            q = f"what majors match: {user_query}"
            results = await loop.run_in_executor(None, lambda: safe_ddg(q, max_results=6) or [])
            for r in results:
                title = (r.get('title') or r.get('heading') or '')
                if title:
                    # split and pick candidate tokens
                    cand = title.split('-')[0].split('|')[0].strip()
                    if len(cand) > 3 and cand not in majors:
                        majors.append(cand)
                if len(majors) >= 5:
                    break
        except Exception:
            majors = []

        # Last resort: return empty list (no hard-coded majors)
        return majors[:5]
    
    async def research_majors(self, major_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Research detailed information about each major.
        
        Args:
            major_names: List of major names to research
            
        Returns:
            Dict keyed by major name, value = {description: str, resources: [urls]}
        """
        results = {}

        async def _generate_resources_via_llm(major: str) -> List[str]:
            """Use LLM to generate search queries, then call safe_ddg and collect URLs."""
            if self.llm_agent is None:
                # fallback: use simple queries without LLM prompt
                queries = [
                    f"{major} youtube videos",
                    f"{major} university websites",
                    f"{major} podcasts personal articles"
                ]
            else:
                # Ask LLM to generate targeted search queries for each category
                try:
                    prompt = (
                        f"Generate 3 search queries to find online resources about the university major '{major}':\n"
                        "1. A query to find YouTube videos or educational video content.\n"
                        "2. A query to find official university program pages or department websites.\n"
                        "3. A query to find podcasts, blogs, or personal articles about this major.\n\n"
                        "Return the queries as a JSON array of 3 strings, e.g.: [\"query1\", \"query2\", \"query3\"]"
                    )
                    resp = await self.llm_agent.run(prompt)
                    import re, json
                    match = re.search(r'\[.*\]', str(resp), flags=re.S)
                    if match:
                        queries = json.loads(match.group(0))
                        if not isinstance(queries, list) or len(queries) < 3:
                            raise ValueError("LLM did not return 3 queries")
                    else:
                        raise ValueError("LLM response did not contain JSON array")
                except Exception:
                    # fallback to simple queries
                    queries = [
                        f"{major} youtube videos",
                        f"{major} university websites",
                        f"{major} podcasts personal articles"
                    ]

            # Execute each query and collect URLs
            urls = []
            loop = asyncio.get_event_loop()
            for q in queries[:3]:
                try:
                    results_list = await loop.run_in_executor(None, lambda query=q: safe_ddg(query, max_results=3) or [])
                    for r in results_list:
                        href = r.get('href') or r.get('url') or r.get('link')
                        if href and href not in urls:
                            urls.append(href)
                except Exception:
                    continue
            return urls[:9]  # cap total at ~9 URLs (3 per category)

        for major_name in major_names:
            # Step 1: Generate description via LLM (no web search for description)
            description = ""
            if self.llm_agent is not None:
                try:
                    prompt = (
                        f"Provide a concise 2-4 sentence introduction to the university major '{major_name}'. "
                        "Include typical topics studied and common career outcomes. Return plain text only."
                    )
                    resp = await self.llm_agent.run(prompt)
                    text = str(resp or "").strip()
                    # Take first paragraph
                    if "\n\n" in text:
                        description = text.split("\n\n")[0].strip()
                    elif "\n" in text:
                        description = text.split("\n")[0].strip()
                    else:
                        description = text
                except Exception:
                    description = ""

            # Step 2: Generate resource URLs via LLM prompts + web search
            resources = await _generate_resources_via_llm(major_name)

            results[major_name] = {
                'description': description,
                'resources': resources
            }

        return results
    
    async def process_query(self, user_query: str) -> Dict[str, Dict[str, Any]]:
        """
        Main entry point: analyze query and research majors.
        
        Args:
            user_query: User's interests and career goals
            
        Returns:
            Dict keyed by major name with {description, resources}
        """
        # Step 1: Analyze interests and get major recommendations
        major_names = await self.analyze_user_interests(user_query)
        
        # Step 2: Research each major in detail
        major_details = await self.research_majors(major_names)
        
        return major_details


# Factory function for easy instantiation
def create_major_research_agent(llm_provider: str = None, model_name: str = None) -> MajorResearchAgent:
    """Create a MajorResearchAgent with a SpoonReactAI instance (if available).

    Falls back to a MajorResearchAgent with no llm_agent if SpoonReactAI isn't installed.
    """
    provider = llm_provider or Config.LLM_PROVIDER
    model = model_name or Config.MODEL_NAME

    if SpoonReactAI is not None:
        try:
            # Validate API keys for chosen provider; if missing, disable LLM usage gracefully
            try:
                Config.validate()
            except Exception as e:
                print(f"⚠️ LLM config validation failed: {e}. Falling back to non-LLM mode.")
                return MajorResearchAgent(llm_agent=None)

            safe_tokens = Config.get_safe_max_tokens(provider)
            # Debug: show what we'll pass to the SDK
            print(f"[LLM Factory] provider={provider}, model={model}, safe_tokens={safe_tokens}")
            # Ensure environment var visible to any underlying SDK that reads it
            try:
                os.environ.setdefault("MAX_TOKENS", str(safe_tokens))
            except Exception:
                pass

            try:
                llm = ChatBot(llm_provider=provider, model_name=model, max_tokens=safe_tokens)
            except TypeError:
                # ChatBot may not accept max_tokens kw; fallback to default constructor
                print("[LLM Factory] ChatBot() rejected max_tokens kwarg; using default constructor")
                llm = ChatBot(llm_provider=provider, model_name=model)
            # Debug: inspect llm object for token-related attrs
            try:
                print("[LLM Factory] llm repr:", repr(llm))
                print("[LLM Factory] llm.max_tokens:", getattr(llm, 'max_tokens', None))
                print("[LLM Factory] llm.config:", getattr(llm, 'config', None))
            except Exception:
                pass

            # Wrap to enforce safe max_tokens at call time
            try:
                llm = TokenEnforcingChatBot(llm, safe_tokens)
            except Exception:
                pass

            llm_agent = SpoonReactAI(llm=llm)
        except Exception as e:
            print(f"⚠️ Could not instantiate SpoonReactAI: {e}. Running without LLM.")
            llm_agent = None
    else:
        llm_agent = None

    return MajorResearchAgent(llm_agent=llm_agent)

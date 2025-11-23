"""Major Research Agent - Researches university majors and academic programs.
Now implemented using SpoonReactAI (ReAct style) for LLM calls.
"""
import asyncio
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# CRITICAL: Import Config FIRST to load .env before SpoonAI initializes
from backend.config import Config
from backend.tools.web_scraper_tool import WebScraperTool
from backend.utils.search_utils import safe_ddg
from backend.utils.llm_utils import TokenEnforcingChatBot

# DO NOT import SpoonAI at module level - it may initialize before env vars are set
# Instead, import inside the factory function after setting environment variables


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
            # Create a default SpoonReactAI if available, otherwise None (delayed import)
            try:
                from spoon_ai.chat import ChatBot
                from spoon_ai.agents import SpoonReactAI
                
                safe_tokens = Config.get_safe_max_tokens(Config.LLM_PROVIDER)
                try:
                    llm = ChatBot(llm_provider=Config.LLM_PROVIDER, model_name=Config.MODEL_NAME, max_tokens=safe_tokens)
                except TypeError:
                    llm = ChatBot(llm_provider=Config.LLM_PROVIDER, model_name=Config.MODEL_NAME)
                self.llm_agent = SpoonReactAI(llm=llm)
            except (ImportError, Exception):
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

Recommend SPECIFIC university major names that align with their interests. 
Return ONLY a Python list of actual major/degree names (not descriptions or article titles), like:
["Fine Arts", "Graphic Design", "Animation"]

Important: 
- Use official major names (e.g., "Computer Science" not "10 Best Tech Degrees")
- Be specific (e.g., "Mechanical Engineering" not "Engineering Majors")
- Return 3-5 majors

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
                    # Filter out non-major titles (like "10 Best...", "Top Careers...")
                    valid_majors = []
                    for item in items:
                        name = str(item).strip()
                        # Skip if it looks like an article title or list
                        if any(skip in name.lower() for skip in ['best', 'top ', 'careers', 'degrees for', '10 ', 'how to']):
                            continue
                        if len(name) > 3:
                            valid_majors.append(name)
                    if valid_majors:
                        return valid_majors[:5]
        except Exception:
            pass

        # Fallback: Use another LLM prompt to extract major names from user query
        if self.llm_agent is not None:
            try:
                fallback_prompt = f"""Extract specific university major names related to: "{user_query}"

For example:
- "I love drawing" → ["Fine Arts", "Graphic Design", "Animation"]
- "I want to build apps" → ["Computer Science", "Software Engineering"]

Return only a JSON list of 3-5 major names (no explanations):"""
                
                response = await self.llm_agent.run(fallback_prompt)
                import re, json
                match = re.search(r'\[.*\]', str(response), flags=re.S)
                if match:
                    items = json.loads(match.group(0))
                    if isinstance(items, list) and items:
                        return [str(x).strip() for x in items if len(str(x).strip()) > 3][:5]
            except Exception:
                pass

        # Last resort: return generic majors based on keywords in query
        query_lower = user_query.lower()
        fallback_majors = []
        
        keyword_map = {
            'draw': ['Fine Arts', 'Graphic Design', 'Animation'],
            'art': ['Fine Arts', 'Art History', 'Studio Art'],
            'computer': ['Computer Science', 'Information Technology'],
            'business': ['Business Administration', 'Marketing', 'Finance'],
            'engineer': ['Mechanical Engineering', 'Electrical Engineering'],
            'science': ['Biology', 'Chemistry', 'Physics'],
            'write': ['English Literature', 'Creative Writing', 'Journalism'],
            'music': ['Music Performance', 'Music Education', 'Music Production'],
            'teach': ['Education', 'Elementary Education', 'Special Education']
        }
        
        for keyword, majors in keyword_map.items():
            if keyword in query_lower:
                fallback_majors.extend(majors)
                break
        
        # If still empty, return empty list
        return fallback_majors[:3] if fallback_majors else []
    
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
        
        # Step 3: Save results to database
        self._save_to_database(user_query, major_details)
        
        return major_details

    def _save_to_database(self, user_query: str, major_details: Dict[str, Dict[str, Any]]):
        """Save major research results to JSON database file."""
        try:
            # Create database directory if it doesn't exist
            db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database')
            os.makedirs(db_dir, exist_ok=True)
            
            # Create timestamped filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"majors_{timestamp}.json"
            filepath = os.path.join(db_dir, filename)
            
            # Prepare data structure
            data = {
                'timestamp': datetime.now().isoformat(),
                'user_query': user_query,
                'majors': major_details
            }
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Also save as latest.json for easy access
            latest_path = os.path.join(db_dir, 'majors_latest.json')
            with open(latest_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"[Database] Saved major research results to {filename}")
        except Exception as e:
            print(f"[Database] Failed to save results: {e}")


# Factory function for easy instantiation
def create_major_research_agent(llm_provider: str = None, model_name: str = None) -> MajorResearchAgent:
    """Create a MajorResearchAgent with a SpoonReactAI instance (if available).

    Falls back to a MajorResearchAgent with no llm_agent if SpoonReactAI isn't installed.
    """
    provider = llm_provider or Config.LLM_PROVIDER
    model = model_name or Config.MODEL_NAME

    # Try to import SpoonAI (delayed import to ensure env vars are set)
    try:
        from spoon_ai.chat import ChatBot
        from spoon_ai.agents import SpoonReactAI
        spoonai_available = True
    except ImportError:
        spoonai_available = False

    if spoonai_available:
        try:
            # Validate API keys for chosen provider; if missing, disable LLM usage gracefully
            try:
                Config.validate()
            except Exception as e:
                print(f"⚠️ LLM config validation failed: {e}. Falling back to non-LLM mode.")
                return MajorResearchAgent(llm_agent=None)

            # CRITICAL: Set API key in os.environ so spoon_ai can access it
            if provider == "gemini" and Config.GEMINI_API_KEY:
                os.environ["GEMINI_API_KEY"] = Config.GEMINI_API_KEY
                print(f"[LLM Factory] ✅ Set GEMINI_API_KEY in os.environ: {Config.GEMINI_API_KEY[:20]}...")
                print(f"[LLM Factory] ✅ Verify os.environ['GEMINI_API_KEY']: {os.environ.get('GEMINI_API_KEY', 'NOT SET')[:20]}...")
            elif provider == "deepseek" and Config.DEEPSEEK_API_KEY:
                os.environ["DEEPSEEK_API_KEY"] = Config.DEEPSEEK_API_KEY
                print(f"[LLM Factory] ✅ Set DEEPSEEK_API_KEY in os.environ")

            safe_tokens = Config.get_safe_max_tokens(provider)
            # Debug: show what we'll pass to the SDK
            print(f"[LLM Factory] provider={provider}, model={model}, safe_tokens={safe_tokens}")
            print(f"[LLM Factory] About to create ChatBot with llm_provider='{provider}', model_name='{model}'")
            # Ensure environment var visible to any underlying SDK that reads it
            try:
                os.environ.setdefault("MAX_TOKENS", str(safe_tokens))
            except Exception:
                pass

            # Try to pass API key directly to ChatBot
            api_key = Config.GEMINI_API_KEY if provider == "gemini" else Config.DEEPSEEK_API_KEY
            print(f"[LLM Factory] API key to pass: {api_key[:20]}..." if api_key else "[LLM Factory] No API key!")
            
            try:
                # Try with api_key parameter first
                llm = ChatBot(llm_provider=provider, model_name=model, api_key=api_key)
                print("[LLM Factory] ✅ ChatBot created with api_key parameter")
            except TypeError:
                # If ChatBot doesn't accept api_key, try environment variable only
                print("[LLM Factory] ChatBot doesn't accept api_key parameter, trying environment variable")
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

            from spoon_ai.agents import SpoonReactAI
            llm_agent = SpoonReactAI(llm=llm)
        except Exception as e:
            print(f"⚠️ Could not instantiate SpoonReactAI: {e}. Running without LLM.")
            llm_agent = None
    else:
        llm_agent = None

    return MajorResearchAgent(llm_agent=llm_agent)

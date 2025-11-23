"""Career Analysis Agent - Analyzes careers related to university majors.
Now uses SpoonReactAI (ReAct style) for optional LLM reasoning and invokes
`MediaFinderTool` directly for media lookups.
"""

import asyncio
import os
from typing import Dict, Any, List
from spoon_ai.chat import ChatBot
try:
    from spoon_ai.agents import SpoonReactAI
except Exception:
    SpoonReactAI = None

from backend.tools.media_finder_tool import MediaFinderTool
import json
import asyncio
from typing import Optional

from bs4 import BeautifulSoup
from backend.utils.search_utils import safe_ddg, http_get_text
from backend.utils.llm_utils import TokenEnforcingChatBot
from backend.config import Config


class CareerAnalysisAgent:
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

    def __init__(self, llm_agent: object = None):
        if llm_agent is not None:
            self.llm_agent = llm_agent
        else:
            if SpoonReactAI is not None:
                self.llm_agent = SpoonReactAI(
                    llm=ChatBot(llm_provider=Config.LLM_PROVIDER, model_name=Config.MODEL_NAME)
                )
            else:
                self.llm_agent = None

        # Media finder tool used directly
        self.media_finder = MediaFinderTool()

    async def identify_careers(self, major_name: str) -> List[str]:
        """
        Identify career paths for a given major.

        Args:
            major_name: Name of the university major

        Returns:
            List of career titles
        """
        # Prefer LLM-generated career titles
        if self.llm_agent is not None:
            prompt = (
                f"List 3-5 common career titles that graduates with a degree in '{major_name}' pursue. "
                "Return a JSON array of short title strings only, for example: [\"Software Engineer\", \"Data Scientist\"]"
            )
            try:
                resp = await self.llm_agent.run(prompt)
                import re, json
                match = re.search(r'\[.*\]', str(resp), flags=re.S)
                if match:
                    items = json.loads(match.group(0))
                    if isinstance(items, list) and items:
                        return [str(x).strip() for x in items][:5]
            except Exception:
                pass

        # Fallback: use DuckDuckGo search snippets to infer career titles
        careers = []
        try:
            loop = asyncio.get_event_loop()
            query = f"careers for {major_name}"
            results = await loop.run_in_executor(None, lambda: safe_ddg(query, max_results=6) or [])
            for r in results:
                title = (r.get('title') or r.get('heading') or '')
                # simple cleanup: split on common separators
                if title:
                    cand = title.split("-")[0].split("|", 1)[0].strip()
                    if len(cand) > 3 and cand not in careers:
                        careers.append(cand)
                if len(careers) >= 4:
                    break
        except Exception:
            careers = []

        # Last-resort fallback: generic professional titles derived from major name
        if not careers:
            base = major_name.split()[:2]
            base_label = " ".join(base)
            careers = [f"{base_label} Professional", f"{base_label} Specialist"]

        return careers[:5]

    async def analyze_career(self, career_title: str) -> Dict[str, Any]:
        """
        Analyze a specific career in detail.

        Args:
            career_title: Title of the career to analyze

        Returns:
            Detailed career information
        """
        # Collect resources for this career: media (YouTube/podcasts), universities, blogs, other
        resources = await self._collect_resources_for_career(career_title)

        # Ask LLM (if available) to synthesize salary/work info, but do not rely on it for resource discovery
        synthesized = {}
        if self.llm_agent is not None:
            prompt = (
                f"Provide a short JSON with keys salary_range, average_salary, benefits, work_intensity, work_life_balance, growth_potential, job_outlook for '{career_title}'."
            )
            try:
                llm_resp = await self.llm_agent.run(prompt)
                import re
                json_match = re.search(r'\{.*\}', str(llm_resp), flags=re.S)
                if json_match:
                    synthesized = json.loads(json_match.group(0))
            except Exception:
                synthesized = {}

        career_data = {
            "salary_range": synthesized.get("salary_range", ""),
            "average_salary": synthesized.get("average_salary", ""),
            "benefits": synthesized.get("benefits", []),
            "work_intensity": synthesized.get("work_intensity", ""),
            "work_life_balance": synthesized.get("work_life_balance", ""),
            "growth_potential": synthesized.get("growth_potential", ""),
            "job_outlook": synthesized.get("job_outlook", "")
        }

        return {
            "id": career_title.lower().replace(" ", "_"),
            "title": career_title,
            **career_data,
            "resources": resources,
            "professional_resources": resources  # legacy key kept for compatibility
        }

    async def _collect_resources_for_career(self, career_title: str) -> Dict[str, List[Dict[str, str]]]:
        """Collect categorized resources for a career using ddg + media tool where available.

        Returns categories: media (YouTube/podcast), universities, blogs, others
        """
        media = []
        universities = []
        blogs = []
        others = []

        # 1) Use MediaFinderTool for media (if it can)
        try:
            mf = await self.media_finder.execute(career_or_major=career_title, content_type="video")
            for item in mf.get("content", [])[:2]:
                media.append({"type": item.get("type", "video"), "title": item.get("title"), "url": item.get("url")})
        except Exception:
            pass

        # 2) Use DuckDuckGo to find YouTube videos and podcasts
        try:
            loop = asyncio.get_event_loop()

            # YouTube videos
            vq = f"{career_title} interview site:youtube.com"
            vids = await loop.run_in_executor(None, lambda: safe_ddg(vq, max_results=6) or [])
            for r in vids:
                href = r.get("href") or r.get("url") or r.get("link")
                title = r.get("title") or r.get("body") or r.get("snippet")
                if href and "youtube.com" in href and len(media) < 2:
                    media.append({"type": "youtube", "title": title, "url": href})

            # Podcasts
            pq = f"{career_title} podcast interview"
            pods = await loop.run_in_executor(None, lambda: safe_ddg(pq, max_results=6) or [])
            for r in pods:
                href = r.get("href") or r.get("url") or r.get("link")
                title = r.get("title") or r.get("body") or r.get("snippet")
                if href and ("podcast" in (r.get('title','') or '').lower() or 'anchor.fm' in (href or '')) and len(media) < 3:
                    media.append({"type": "podcast", "title": title, "url": href})

            # Universities - prefer .edu / university pages
            uq = f"{career_title} degree program university"
            ures = await loop.run_in_executor(None, lambda: safe_ddg(uq, max_results=10) or [])
            for r in ures:
                href = r.get("href") or r.get("url") or r.get("link")
                title = r.get("title") or r.get("body") or r.get("snippet")
                if href and (".edu" in href or "university" in (title or '').lower() or "faculty" in (title or '').lower()):
                    universities.append({"title": title, "url": href})
                if len(universities) >= 3:
                    break

            # Blogs / personal sites
            bq = f"{career_title} blog personal site"
            bres = await loop.run_in_executor(None, lambda: safe_ddg(bq, max_results=8) or [])
            for r in bres:
                href = r.get("href") or r.get("url") or r.get("link")
                title = r.get("title") or r.get("body") or r.get("snippet")
                if href and ("blog" in (title or '').lower() or "medium.com" in (href or '') or "github.io" in (href or '')):
                    blogs.append({"title": title, "url": href})
                if len(blogs) >= 3:
                    break

            # Other helpful pages
            ores = await loop.run_in_executor(None, lambda: safe_ddg(f"{career_title} professional resources", max_results=6) or [])
            for r in ores:
                href = r.get("href") or r.get("url") or r.get("link")
                title = r.get("title") or r.get("body") or r.get("snippet")
                if href and href not in [u.get("url") for u in universities] and href not in [m.get("url") for m in media]:
                    others.append({"title": title, "url": href})
        except Exception:
            pass

        # Ensure minimum items: try MediaFinderTool for podcasts/videos/universities if missing
        try:
            if len(media) < 2:
                mf2 = await self.media_finder.execute(career_or_major=career_title, content_type="all")
                for item in mf2.get("content", [])[: (2 - len(media))]:
                    media.append({"type": item.get("type","video"), "title": item.get("title"), "url": item.get("url")})
            if len(universities) < 2:
                mfu = await self.media_finder.execute(career_or_major=career_title, content_type="university")
                for u in mfu.get("content", [])[: (2 - len(universities))]:
                    universities.append({"title": u.get("title"), "url": u.get("url")})
        except Exception:
            pass

        return {
            "media": media,
            "universities": universities,
            "blogs": blogs,
            "others": others
        }

    async def _fetch_web_summary(self, query: str) -> Dict[str, str]:
        """Fetch a short web summary for `query` using DuckDuckGo or Wikipedia as fallback."""
        # Try duckduckgo-search
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, lambda: safe_ddg(query, max_results=5))

            # Prefer Wikipedia link
            wiki_url = None
            snippet = None
            for r in results or []:
                href = r.get("href") or r.get("url") or r.get("link")
                title = r.get("title", "")
                body = r.get("body") or r.get("snippet") or ""
                if href and "wikipedia.org" in href:
                    wiki_url = href
                    snippet = body
                    break
            if wiki_url:
                # In many environments Wikipedia blocks direct scraping (403).
                # Prefer returning the search snippet rather than attempting
                # a full fetch which may produce repeated 403s. If a more
                # reliable domain is present in results (whitelist), fetch that.
                summary = snippet or ""
                # Look for a friendly domain to fetch instead of wikipedia
                from urllib.parse import urlparse
                whitelist = ("google.com", "bbc.com", "github.com", "example.com")
                for r in results or []:
                    href = r.get('href') or r.get('url') or r.get('link')
                    if not href:
                        continue
                    try:
                        hostname = urlparse(href).hostname or ""
                    except Exception:
                        hostname = ""
                    for good in whitelist:
                        if good in hostname:
                            try:
                                text = await http_get_text(href)
                                soup = BeautifulSoup(text, "html.parser")
                                p = soup.find("p")
                                summary = p.get_text().strip() if p else summary
                                return {"source": href, "summary": summary}
                            except Exception:
                                # ignore and continue to next candidate
                                summary = summary
                                break

                # Default: return the wikipedia link with the snippet (no fetch)
                return {"source": wiki_url, "summary": summary}

            # If no wikipedia, return first snippet
            if results:
                first = results[0]
                return {"source": first.get("href") or first.get("url") or "", "summary": first.get("body") or first.get("snippet") or ""}
        except Exception:
            pass

        # Fallback: try Wikipedia REST via httpx
        try:
            search_url = f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}"
            try:
                text = await http_get_text(search_url)
                soup = BeautifulSoup(text, "html.parser")
                p = soup.find("p")
                summary = p.get_text().strip() if p else ""
                return {"source": search_url, "summary": summary}
            except Exception:
                pass
        except Exception:
            pass

        return {"source": "", "summary": ""}

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
def create_career_analysis_agent(llm_provider: str = None, model_name: str = None) -> CareerAnalysisAgent:
    """Create a CareerAnalysisAgent with an optional SpoonReactAI instance."""
    provider = llm_provider or Config.LLM_PROVIDER
    model = model_name or Config.MODEL_NAME

    if SpoonReactAI is not None:
        try:
            try:
                Config.validate()
            except Exception as e:
                print(f"⚠️ LLM config validation failed: {e}. Falling back to non-LLM mode.")
                return CareerAnalysisAgent(llm_agent=None)

            safe_tokens = Config.get_safe_max_tokens(provider)
            print(f"[LLM Factory] provider={provider}, model={model}, safe_tokens={safe_tokens}")
            try:
                os.environ.setdefault("MAX_TOKENS", str(safe_tokens))
            except Exception:
                pass

            try:
                llm = ChatBot(llm_provider=provider, model_name=model, max_tokens=safe_tokens)
            except TypeError:
                print("[LLM Factory] ChatBot() rejected max_tokens kwarg; using default constructor")
                llm = ChatBot(llm_provider=provider, model_name=model)

            # Debug: inspect llm object for token-related attrs
            try:
                print("[LLM Factory] llm repr:", repr(llm))
                print("[LLM Factory] llm.max_tokens:", getattr(llm, 'max_tokens', None))
                print("[LLM Factory] llm.config:", getattr(llm, 'config', None))
            except Exception:
                pass

            # Wrap the raw ChatBot with a token-enforcing wrapper to guarantee
            # a provider-safe `max_tokens` is present at call time.
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

    return CareerAnalysisAgent(llm_agent=llm_agent)

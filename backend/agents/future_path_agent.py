"""Future Path Agent - Projects career progression and future development paths.
Now uses SpoonReactAI (ReAct style) for optional LLM calls and calls
`LinkedInAnalyzerTool` directly for simulated LinkedIn data.
"""

import asyncio
from typing import Dict, Any, List
from spoon_ai.chat import ChatBot
try:
    from spoon_ai.agents import SpoonReactAI
except Exception:
    SpoonReactAI = None

from backend.tools.linkedin_analyzer_tool import LinkedInAnalyzerTool
from backend.config import Config
from backend.tools.media_finder_tool import MediaFinderTool
from backend.utils.search_utils import safe_ddg
import os
from backend.utils.llm_utils import TokenEnforcingChatBot

class FuturePathAgent:
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

    def __init__(self, llm_agent: object = None):
        if llm_agent is not None:
            self.llm_agent = llm_agent
        else:
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

        # Tool used directly for simulated LinkedIn analysis
        self.linkedin_tool = LinkedInAnalyzerTool()
        # Media & web lookup tool
        self.media_finder = MediaFinderTool()

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
        progression_data = await self.linkedin_tool.execute(
            career_title=career_title,
            years_experience=years
        )
        
        if progression_data.get("success"):
            stats = progression_data["statistics"]
            # Collect web/media resources related to this career (YouTube/podcasts, universities, blogs)
            resources = await self._collect_resources_for_career(career_title)

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
                "insights": self._generate_insights(stats),
                "resources": resources
            }
        
        return {}

    async def _collect_resources_for_career(self, career_title: str) -> Dict[str, List[Dict[str, str]]]:
        """Collect media/university/blog resources for a career.

        Returns categories: media (YouTube/podcast), universities, blogs, others
        """
        media = []
        universities = []
        blogs = []
        others = []

        # 1) Use MediaFinderTool first to get any known videos or channels
        try:
            mf = await self.media_finder.execute(career_or_major=career_title, content_type="video")
            for item in mf.get("content", [])[:2]:
                media.append({"type": item.get("type", "video"), "title": item.get("title"), "url": item.get("url")})
        except Exception:
            pass

        # 2) Use DuckDuckGo to find resources
        try:
            loop = asyncio.get_event_loop()
            # YouTube interviews / talks
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
                if href and len(media) < 3:
                    media.append({"type": "podcast", "title": title, "url": href})

            # University program pages (prefer .edu or known university domains)
            uq = f"{career_title} degree program university"
            ures = await loop.run_in_executor(None, lambda: safe_ddg(uq, max_results=10) or [])
            for r in ures:
                href = r.get("href") or r.get("url") or r.get("link")
                title = r.get("title") or r.get("body") or r.get("snippet")
                if href and (".edu" in href or "university" in (title or '').lower()):
                    universities.append({"title": title, "url": href})
                if len(universities) >= 3:
                    break

            # Blogs and personal sites
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

        # 3) Supplement with media_finder if lists are short
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

        return {"media": media, "universities": universities, "blogs": blogs, "others": others}
    
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
def create_future_path_agent(llm_provider: str = None, model_name: str = None) -> FuturePathAgent:
    """Create a FuturePathAgent with an optional SpoonReactAI instance."""
    provider = llm_provider or Config.LLM_PROVIDER
    model = model_name or Config.MODEL_NAME

    if SpoonReactAI is not None:
        try:
            try:
                Config.validate()
            except Exception as e:
                print(f"⚠️ LLM config validation failed: {e}. Falling back to non-LLM mode.")
                return FuturePathAgent(llm_agent=None)

            safe_tokens = Config.get_safe_max_tokens(provider)
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

            # Wrap ChatBot to enforce safe max_tokens at call time
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

    return FuturePathAgent(llm_agent=llm_agent)

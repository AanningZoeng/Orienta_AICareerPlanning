"""Career Analysis Agent - Analyzes careers related to university majors.
Now uses SpoonReactAI (ReAct style) for optional LLM reasoning and invokes
`MediaFinderTool` directly for media lookups.
"""

import asyncio
import os
import json
import glob
import sqlite3
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Third-party imports for vector similarity
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    print("Warning: scikit-learn not installed. Job database features will be disabled.")
    TfidfVectorizer = None
    cosine_similarity = None

# CRITICAL: Import Config and tools FIRST before SpoonAI
# Try absolute import first, then relative import as fallback
try:
    from backend.tools.media_finder_tool import MediaFinderTool
except ImportError:
    try:
        from tools.media_finder_tool import MediaFinderTool
    except ImportError:
        # If both fail, create a dummy MediaFinderTool
        print("Warning: MediaFinderTool not available. Media features will be disabled.")
        MediaFinderTool = None

# Import SpoonAI after backend imports
from spoon_ai.chat import ChatBot
try:
    from spoon_ai.agents import SpoonReactAI
except Exception:
    SpoonReactAI = None

from bs4 import BeautifulSoup

# Try absolute import first, then relative import
try:
    from backend.utils.search_utils import safe_ddg, http_get_text
    from backend.utils.llm_utils import TokenEnforcingChatBot
    from backend.config import Config
except ImportError:
    from utils.search_utils import safe_ddg, http_get_text
    from utils.llm_utils import TokenEnforcingChatBot
    from config import Config


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

    def __init__(self, llm_agent: object = None, db_path: str = None):
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
        self.media_finder = MediaFinderTool() if MediaFinderTool is not None else None
        
        # Database path setup for real job data
        if db_path:
            self.db_path = Path(db_path)
        else:
            # Default to job_info.db in the same directory as this file
            self.db_path = Path(__file__).resolve().parent / "job_info.db"

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
                f"List exactly 3 common career titles that graduates with a degree in '{major_name}' pursue. "
                "Return a JSON array of short title strings only, for example: [\"Software Engineer\", \"Data Scientist\", \"Product Manager\"]"
            )
            try:
                resp = await self.llm_agent.run(prompt)
                import re, json
                match = re.search(r'\[.*\]', str(resp), flags=re.S)
                if match:
                    items = json.loads(match.group(0))
                    if isinstance(items, list) and items:
                        return [str(x).strip() for x in items][:3]
            except Exception:
                pass

        # Fallback: use predefined career mapping for common majors
        major_lower = major_name.lower()
        career_mapping = {
            'computer science': ['Software Engineer', 'Data Scientist', 'Software Developer'],
            'mathematics': ['Data Analyst', 'Actuary', 'Financial Analyst'],
            'computer engineering': ['Hardware Engineer', 'Embedded Systems Engineer', 'Network Engineer'],
            'electrical engineering': ['Electrical Engineer', 'Electronics Engineer', 'Power Systems Engineer'],
            'mechanical engineering': ['Mechanical Engineer', 'Manufacturing Engineer', 'Design Engineer'],
            'business': ['Business Analyst', 'Management Consultant', 'Product Manager'],
            'economics': ['Economist', 'Financial Analyst', 'Data Analyst'],
            'biology': ['Research Scientist', 'Biotech Researcher', 'Lab Technician'],
            'chemistry': ['Chemist', 'Research Scientist', 'Chemical Engineer'],
            'physics': ['Physicist', 'Research Scientist', 'Data Scientist'],
            'psychology': ['Psychologist', 'Counselor', 'Human Resources Specialist'],
        }
        
        # Try to find a match in the mapping
        for key, careers in career_mapping.items():
            if key in major_lower:
                return careers[:3]
        
        # Last-resort fallback: generic professional titles
        base = major_name.split()[:2]
        base_label = " ".join(base)
        return [f"{base_label} Specialist", f"{base_label} Analyst", f"{base_label} Consultant"]

    # --- Job Database Helper Methods (from agent2) ---

    def _parse_salary(self, salary_str: str) -> List[float]:
        """Parses salary string like '$100k - $150k' into float list."""
        if not salary_str:
            return []
        
        s = salary_str.lower().replace(',', '')
        numbers = re.findall(r'\d+(?:\.\d+)?', s)
        if not numbers:
            return []
        
        parsed_nums = []
        for num in numbers:
            val = float(num)
            # Simple heuristic: if 'k' is in string and value < 1000, multiply by 1000
            if 'k' in s and val < 1000: 
                val *= 1000
            parsed_nums.append(val)
            
        return parsed_nums

    def _vec_similarity(self, target_job: str, threshold: float = 0.2) -> List[str]:
        """Calculates TF-IDF cosine similarity to find matching job titles in DB."""
        if not self.db_path.exists():
            return []
        
        if TfidfVectorizer is None:
            return []

        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = 'select "Job Title" from jobs'
            cursor.execute(query)
            raw_data = cursor.fetchall()
            
            db_titles = [item[0] for item in raw_data if item[0] is not None]
            
            if not db_titles:
                return []

            all_documents = [target_job] + db_titles
            
            tfidf_vectorizer = TfidfVectorizer()
            tfidf_matrix = tfidf_vectorizer.fit_transform(all_documents)
            
            # Compute similarity between target (index 0) and all others
            cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
            scores = cosine_sim[0]
            
            results = list(zip(db_titles, scores))
            # Sort by score descending
            sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
            
            filtered_job_list = [
                title for title, score in sorted_results 
                if score >= threshold
            ]
            return filtered_job_list

        except Exception as e:
            print(f"[CareerAnalysisAgent] Similarity calculation error: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def _fetch_job_db_data(self, target_job: str) -> Dict[str, Any]:
        """Query job database and return real salary data and job examples."""
        default_result = {
            "salary": {"min": 0, "max": 0, "currency": "USD"},
            "job_examples": [],
            "db_match_count": 0
        }

        if not self.db_path.exists():
            return default_result

        conn = None
        try:
            # 1. Get similar titles using TF-IDF
            similar_jobs = self._vec_similarity(target_job, threshold=0.2)
            
            if not similar_jobs:
                return default_result

            if len(similar_jobs) > 10:
                similar_jobs = similar_jobs[:10]

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 2. SQL Query using 'IN' clause
            placeholders = ','.join('?' for _ in similar_jobs)
            query = f'''
            SELECT "Job Title", Company, "Salary Range", "Job Description" 
            FROM jobs
            WHERE "Job Title" IN ({placeholders})
            '''
            
            cursor.execute(query, similar_jobs)
            rows = cursor.fetchall()
            
            all_salaries = []
            examples = []
            
            for row in rows:
                title, company, salary_text, desc = row
                
                # Parse salary
                nums = self._parse_salary(salary_text)
                all_salaries.extend(nums)
                
                # Format Description (truncate if too long)
                clean_desc = desc[:300] + "..." if desc and len(desc) > 300 else desc

                examples.append({
                    "job_title": title,
                    "company": company,
                    "description": clean_desc,
                    "salary_range": salary_text
                })

            salary_min = min(all_salaries) if all_salaries else 0
            salary_max = max(all_salaries) if all_salaries else 0

            return {
                "salary": {
                    "min": salary_min,
                    "max": salary_max,
                    "currency": "USD"
                },
                "job_examples": examples[:5],  # Limit to 5 examples
                "db_match_count": len(examples)
            }

        except Exception as e:
            print(f"[CareerAnalysisAgent] Database query error: {e}")
            return default_result
        finally:
            if conn:
                conn.close()

    async def analyze_career_simple(self, career_title: str, major_name: str = "") -> Dict[str, Any]:
        """Analyze a career and return integrated data structure.
        
        Args:
            career_title: The career to analyze
            major_name: The major this career relates to (for context)
        
        Returns:
            Dict with:
            - description: LLM-generated text
            - resources: list of URLs from web search
            - salary: real data from job database {min, max, currency}
            - job_examples: list of real job postings from database
            - db_match_count: number of matching jobs found
        """
        # Step 1: Generate description via LLM
        description = ""
        if self.llm_agent is not None:
            try:
                context = f" for graduates with a {major_name} degree" if major_name else ""
                prompt = (
                    f"Provide a concise 2-4 sentence description of the career '{career_title}'{context}. "
                    "Include typical responsibilities, work environment, and career growth potential. "
                    "Do NOT say 'I don't have a specific tool' or similar meta-commentary. "
                    "Just provide the factual description directly. "
                    "Return plain text only (no markdown, no formatting)."
                )
                resp = await self.llm_agent.run(prompt)
                text = str(resp or "").strip()
                
                # Filter out meta-commentary responses
                if any(phrase in text.lower() for phrase in [
                    "i don't have", "i do not have", "specific tool", 
                    "general knowledge", "based on my knowledge"
                ]):
                    # Regenerate with more direct prompt
                    direct_prompt = (
                        f"Write a 2-3 sentence description of the {career_title} career. "
                        f"What does a {career_title} do? What skills are needed? "
                        "Be direct and factual."
                    )
                    resp = await self.llm_agent.run(direct_prompt)
                    text = str(resp or "").strip()
                
                # Take first paragraph
                if "\n\n" in text:
                    description = text.split("\n\n")[0].strip()
                elif "\n" in text:
                    description = text.split("\n")[0].strip()
                else:
                    description = text
                
                # Final validation: reject if still contains meta-commentary
                if any(phrase in description.lower() for phrase in [
                    "i don't have", "i do not have", "specific tool"
                ]):
                    description = ""
                    
            except Exception as e:
                print(f"[CareerAnalysisAgent] LLM description failed for {career_title}: {e}")
                description = ""
        
        # Step 2: Generate resource URLs via LLM-generated search queries + DuckDuckGo
        resources = await self._generate_career_resources(career_title, major_name)
        
        # Step 3: Query job database for real salary and job examples (async executor)
        loop = asyncio.get_event_loop()
        db_data = await loop.run_in_executor(None, self._fetch_job_db_data, career_title)
        
        return {
            'description': description,
            'resources': resources,
            'salary': db_data.get('salary', {"min": 0, "max": 0, "currency": "USD"}),
            'job_examples': db_data.get('job_examples', []),
            'db_match_count': db_data.get('db_match_count', 0)
        }
    
    async def _generate_career_resources(self, career_title: str, major_name: str = "") -> List[str]:
        """Use LLM to generate search queries, then collect URLs via DuckDuckGo."""
        # Ask LLM to generate 3 targeted search queries
        queries = []
        if self.llm_agent is not None:
            try:
                context = f" for {major_name} graduates" if major_name else ""
                prompt = (
                    f"Generate 3 search queries to find online resources about the career '{career_title}'{context}:\n"
                    "1. A query to find professional organizations, associations, or industry websites.\n"
                    "2. A query to find salary data, job outlook reports, or career guides.\n"
                    "3. A query to find YouTube videos, podcasts, or blogs about this career.\n\n"
                    'Return the queries as a JSON array of 3 strings, e.g.: ["query1", "query2", "query3"]'
                )
                resp = await self.llm_agent.run(prompt)
                import re
                match = re.search(r'\[.*\]', str(resp), flags=re.S)
                if match:
                    queries = json.loads(match.group(0))
                    if not isinstance(queries, list) or len(queries) < 3:
                        raise ValueError("LLM did not return 3 queries")
            except Exception as e:
                print(f"[CareerAnalysisAgent] LLM query generation failed for {career_title}: {e}")
                queries = []
        
        # Fallback: use simple queries if LLM failed
        if not queries:
            queries = [
                f"{career_title} professional association",
                f"{career_title} salary data career outlook",
                f"{career_title} youtube interview blog"
            ]
        
        # Execute each query and collect unique URLs
        urls = []
        loop = asyncio.get_event_loop()
        for q in queries[:3]:
            try:
                results = await loop.run_in_executor(None, lambda query=q: safe_ddg(query, max_results=3) or [])
                for r in results:
                    href = r.get('href') or r.get('url') or r.get('link')
                    if href and href not in urls:
                        urls.append(href)
            except Exception as e:
                print(f"[CareerAnalysisAgent] DuckDuckGo search failed for query '{q}': {e}")
                continue
        
        return urls[:9]  # Cap at 9 URLs total (3 per category)

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
        if self.media_finder is not None:
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
        if self.media_finder is not None:
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

    async def process_query(self, major_json_path: str = None) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Read major JSON file and generate career analysis for each major.
        
        Args:
            major_json_path: Path to specific major JSON file. If None, uses latest.
        
        Returns:
            Dict[major_name, Dict[career_title, {description, resources}]]
        """
        # Step 1: Load major data from JSON
        major_data = self._load_major_json(major_json_path)
        if not major_data:
            print("[CareerAnalysisAgent] No major data found")
            return {}
        
        majors = major_data.get('majors', {})
        user_query = major_data.get('user_query', '')
        
        # Step 2: Process each major
        results = {}
        for major_name in majors.keys():
            print(f"[CareerAnalysisAgent] Processing major: {major_name}")
            
            # Identify 3 careers for this major
            career_titles = await self.identify_careers(major_name)
            
            # Analyze each career
            major_careers = {}
            for career_title in career_titles:
                print(f"[CareerAnalysisAgent]   Analyzing career: {career_title}")
                career_data = await self.analyze_career_simple(career_title, major_name)
                major_careers[career_title] = career_data
            
            results[major_name] = major_careers
        
        # Step 3: Save results to database
        self._save_to_database(user_query, results, major_data.get('timestamp', ''))
        
        return results
    
    def _load_major_json(self, json_path: str = None) -> Dict[str, Any]:
        """Load major research data from JSON file.
        
        Args:
            json_path: Specific file path. If None, loads majors_latest.json
        
        Returns:
            Parsed JSON data or empty dict if failed
        """
        try:
            db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database')
            
            if json_path is None:
                # Use latest file
                json_path = os.path.join(db_dir, 'majors_latest.json')
            
            if not os.path.exists(json_path):
                print(f"[CareerAnalysisAgent] JSON file not found: {json_path}")
                return {}
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"[CareerAnalysisAgent] Loaded major data from {os.path.basename(json_path)}")
            return data
        
        except Exception as e:
            print(f"[CareerAnalysisAgent] Failed to load JSON: {e}")
            return {}
    
    def _save_to_database(self, user_query: str, career_data: Dict[str, Dict[str, Dict[str, Any]]], source_timestamp: str = ""):
        """Save career analysis results to JSON database.
        
        Format: {major: {career: {description, resources, salary, job_examples, db_match_count}}}
        
        Args:
            user_query: Original user query from major research
            career_data: Dict[major_name, Dict[career_title, {description, resources, salary, job_examples, db_match_count}]]
            source_timestamp: Timestamp from source major JSON file
        """
        try:
            db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database')
            os.makedirs(db_dir, exist_ok=True)
            
            # Create timestamped filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"careers_{timestamp}.json"
            filepath = os.path.join(db_dir, filename)
            
            # Prepare data structure in the required format:
            # {major: {career: {description, resources, salary, job_examples, db_match_count}}}
            formatted_data = {}
            for major_name, careers_dict in career_data.items():
                formatted_data[major_name] = {}
                for career_title, career_info in careers_dict.items():
                    # Ensure all required fields are present
                    formatted_data[major_name][career_title] = {
                        'description': career_info.get('description', ''),
                        'resources': career_info.get('resources', []),
                        'salary': career_info.get('salary', {'min': 0, 'max': 0, 'currency': 'USD'}),
                        'job_examples': career_info.get('job_examples', []),
                        'db_match_count': career_info.get('db_match_count', 0)
                    }
            
            # Wrap with metadata
            data = {
                'timestamp': datetime.now().isoformat(),
                'source_timestamp': source_timestamp,
                'user_query': user_query,
                'careers': formatted_data
            }
            
            # Write to timestamped file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Also save as careers_latest.json
            latest_path = os.path.join(db_dir, 'careers_latest.json')
            with open(latest_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"[Database] Saved career analysis results to {filename}")
            print(f"[Database] Format: {{major: {{career: {{description, resources, salary, job_examples, db_match_count}}}}}}")
        
        except Exception as e:
            print(f"[Database] Failed to save career results: {e}")

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
                print(f"[WARNING] LLM config validation failed: {e}. Falling back to non-LLM mode.")
                return CareerAnalysisAgent(llm_agent=None)

            # CRITICAL: Set API key in os.environ so spoon_ai can access it
            if provider == "gemini" and Config.GEMINI_API_KEY:
                os.environ["GEMINI_API_KEY"] = Config.GEMINI_API_KEY
            elif provider == "deepseek" and Config.DEEPSEEK_API_KEY:
                os.environ["DEEPSEEK_API_KEY"] = Config.DEEPSEEK_API_KEY

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
            print(f"[WARNING] Could not instantiate SpoonReactAI: {e}. Running without LLM.")
            llm_agent = None
    else:
        llm_agent = None

    return CareerAnalysisAgent(llm_agent=llm_agent)


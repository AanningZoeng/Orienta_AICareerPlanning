"""Simple test runner to call backend agents directly (bypass frontend).

Usage:
  python spoonTest.py

This script will:
 - load environment variables via python-dotenv
 - create MajorResearchAgent, CareerAnalysisAgent, FuturePathAgent via their factories
 - call a small set of async methods and print results

This helps verify whether the agents operate correctly in isolation.
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure project package is importable when this script runs from parent directory.
# If the repo folder 'Orienta_AICareerPlanning' exists as a sibling, add it to sys.path.
HERE = Path(__file__).resolve().parent
repo_folder = HERE / "Orienta_AICareerPlanning"
if repo_folder.exists() and (repo_folder / "backend").exists():
    sys.path.insert(0, str(repo_folder))
    print(f"Added project path to sys.path: {repo_folder}")
else:
    # Search for a child directory that contains `backend`
    found = False
    for candidate in HERE.iterdir():
        if candidate.is_dir() and (candidate / "backend").exists():
            sys.path.insert(0, str(candidate))
            print(f"Added detected project path to sys.path: {candidate}")
            found = True
            break
    if not found:
        print("Warning: could not auto-detect project path. If imports fail, run this script from the repo root or set PYTHONPATH.")

load_dotenv()

def safe_import(name: str):
    try:
        parts = name.split(".")
        mod = __import__(".".join(parts[:-1]) if len(parts) > 1 else parts[0], fromlist=[parts[-1]])
        return getattr(mod, parts[-1])
    except Exception as e:
        print(f"⚠️ 无法导入 {name}: {e}")
        return None


async def run_agent_checks():
    print("\n== Agent Sanity Check ==\n")

    try:
        print("[NetworkTest] DuckDuckGo search...")
        # Use the project's safe wrapper (supports ddgs and duckduckgo_search versions)
        from backend.utils.search_utils import safe_ddg, http_get_text
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, lambda: safe_ddg("Computer Science careers site:wikipedia.org", max_results=3) or [])
        print("[ddg] ok:", len(results))
    except Exception as e:
        print("[ddg] failed:", e)

    try:
        print("[NetworkTest] httpx + BeautifulSoup fetch...")
        # Reuse shared http_get_text helper to centralize headers and retries
        from backend.utils.search_utils import http_get_text
        try:
            text = await http_get_text("https://en.wikipedia.org/wiki/Computer_science", timeout=10, retries=3)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(text, "html.parser")
            p = soup.find("p")
            txt = p.get_text().strip() if p else ""
            print("[bs4] ok:", bool(txt))
        except Exception as e:
            print("[bs4] http error:", e)
    except Exception as e:
        print("[bs4] failed:", e)

    try:
        print("[API] POST /api/analyze test...")
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            h = await client.get("http://localhost:5000/api/health")
            print("[API] health:", h.status_code)
            if h.status_code == 200:
                r = await client.post("http://localhost:5000/api/analyze", json={"query": "what is obama's last name?"})
                print("[API] status:", r.status_code)
            else:
                print("[API] skipped analyze, server not healthy")
        try:
            if h.status_code == 200:
                data = r.json()
                print("[API] keys:", list(data.keys()))
                print("[API] majors_count:", len(data.get("majors", [])))
        except Exception as e:
            print("[API] parse failed:", e)
            print("[API] text:", r.text[:200])
    except Exception as e:
        print("[API] request failed:", e)

    # Import factories lazily to avoid top-level import errors
    try:
        from backend.agents.major_research_agent import create_major_research_agent
        from backend.agents.career_analysis_agent import create_career_analysis_agent
        from backend.agents.future_path_agent import create_future_path_agent
    except Exception as e:
        print("Error importing agent factories:", e)
        return

    # Create agents (they will read Config defaults internally)
    major_agent = create_major_research_agent()
    career_agent = create_career_analysis_agent()
    future_agent = create_future_path_agent()

    # 1) MajorResearchAgent: analyze a sample query
    try:
        print("[MajorResearchAgent] Running process_query with sample input...")
        majors_result = await major_agent.process_query("I like programming, AI, and problem solving")
        print("MajorResearchAgent result (summary):")
        print("  recommended count:", majors_result.get("count"))
        if majors_result.get("recommended_majors"):
            for m in majors_result.get("recommended_majors")[:2]:
                print("   -", m.get("name"))
    except Exception as e:
        print("MajorResearchAgent failed:", e)

    # 2) CareerAnalysisAgent: analyze careers for a known major
    try:
        print("\n[CareerAnalysisAgent] Running process_major for 'Computer Science'...")
        careers_result = await career_agent.process_major("Computer Science")
        print("CareerAnalysisAgent result (summary):")
        print("  major:", careers_result.get("major"))
        print("  careers count:", careers_result.get("count"))
        if careers_result.get("careers"):
            for c in careers_result.get("careers")[:2]:
                print("   -", c.get("title"), ": avg salary ->", c.get("average_salary"))
    except Exception as e:
        print("CareerAnalysisAgent failed:", e)

    # 3) FuturePathAgent: project future for a known career
    try:
        print("\n[FuturePathAgent] Running analyze_progression for 'Software Engineer'...")
        future_result = await future_agent.analyze_progression("Software Engineer", years=5)
        print("FuturePathAgent result (summary):")
        if future_result:
            print("  career:", future_result.get("career"))
            stats = future_result.get("statistics", {})
            print("  promoted%:", stats.get("promoted", {}).get("percentage") if isinstance(stats.get("promoted"), dict) else stats.get("promoted"))
    except Exception as e:
        print("FuturePathAgent failed:", e)


"""
Main entry: run the agent sanity checks using the run_agent_checks coroutine.
This uses an explicit event loop and cleans up pending tasks to avoid
``No event loop available for async cleanup`` errors on Windows.
"""

def main():
    print("Starting agent checks. Make sure dependencies are installed (pip install -r requirements.txt).")

    # On Windows, some libraries work better with the SelectorEventLoop
    if sys.platform.startswith("win"):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass

    # Use an explicit event loop and close it cleanly to avoid "No event loop available for async cleanup"
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_agent_checks())
    finally:
        try:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        except Exception:
            # If gathering/cancelling fails, ignore and proceed to close loop
            pass
        loop.close()


if __name__ == '__main__':
    main()
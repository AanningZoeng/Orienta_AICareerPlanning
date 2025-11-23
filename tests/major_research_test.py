r"""Test MajorResearchAgent output shape and content.

Run with: python tests\major_research_test.py

This script:
- Instantiates MajorResearchAgent via factory (uses LLM if configured, otherwise falls back)
- Calls analyze_user_interests() with a sample query
- Calls research_majors() for the returned majors
- Verifies returned structures contain expected keys and types
"""
import sys
import os
import asyncio
import json

# Ensure project root on path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# CRITICAL: Import Config FIRST to load .env before SpoonAI classes initialize
from backend.config import Config
from backend.agents.major_research_agent import create_major_research_agent


async def run_test():
    print("Creating MajorResearchAgent (LLM may be disabled if config missing)...")
    agent = create_major_research_agent()

    sample_query = "I enjoy programming, algorithms, and math. What majors fit me?"
    print("Calling process_query() for full workflow...")
    result = await agent.process_query(sample_query)

    if not isinstance(result, dict):
        raise AssertionError("process_query must return a dict keyed by major name")

    print(f"process_query returned {len(result)} majors")

    for major_name, major_data in result.items():
        print(f"\n{'='*60}")
        print(f"Major: {major_name}")
        print(f"{'='*60}")
        
        if not isinstance(major_data, dict):
            raise AssertionError(f"Value for {major_name} must be a dict")
        if 'description' not in major_data:
            raise AssertionError(f"Missing 'description' in {major_name}")
        if 'resources' not in major_data:
            raise AssertionError(f"Missing 'resources' in {major_name}")
        if not isinstance(major_data['resources'], list):
            raise AssertionError(f"'resources' must be a list in {major_name}")

        # Print full description
        desc = major_data.get('description', '')
        print(f"\nDescription ({len(desc)} chars):")
        print(desc if desc else "(empty)")
        
        # Print all resource URLs
        resources = major_data.get('resources', [])
        print(f"\nResources ({len(resources)} URLs):")
        if resources:
            for i, url in enumerate(resources, 1):
                print(f"  {i}. {url}")
        else:
            print("  (no resources)")
        print()

    # summary
    summary = {
        'num_majors': len(result),
        'major_names': list(result.keys()),
        'sample_data': {k: {'desc_len': len(v.get('description','')), 'resources_count': len(v.get('resources',[]))} for k, v in list(result.items())[:2]}
    }

    print("Test succeeded. Summary:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    print("\n[Database] Check backend/database/ folder for saved JSON files:")
    print("  - majors_<timestamp>.json (timestamped version)")
    print("  - majors_latest.json (always points to most recent)")




def main():
    try:
        asyncio.run(run_test())
        print("\nAll checks passed.")
        sys.exit(0)
    except AssertionError as e:
        print("Assertion failed:", e)
        sys.exit(2)
    except Exception as e:
        print("Unexpected error:", type(e).__name__, e)
        sys.exit(3)


if __name__ == '__main__':
    main()

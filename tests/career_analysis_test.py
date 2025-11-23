"""Test script for CareerAnalysisAgent with JSON database integration.

This script:
1. Reads the latest majors JSON file
2. Generates 3 careers for each major
3. For each career, generates description (LLM) and resources (web search)
4. Saves results to careers_<timestamp>.json
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# CRITICAL: Import Config FIRST to load .env before SpoonAI classes initialize
from backend.config import Config

# CRITICAL: Set environment variables explicitly before creating agents
if Config.GEMINI_API_KEY:
    os.environ["GEMINI_API_KEY"] = Config.GEMINI_API_KEY
    print(f"✅ Set GEMINI_API_KEY in os.environ")
if Config.DEEPSEEK_API_KEY:
    os.environ["DEEPSEEK_API_KEY"] = Config.DEEPSEEK_API_KEY

from backend.agents.career_analysis_agent import create_career_analysis_agent


async def test_career_analysis():
    """Test CareerAnalysisAgent with JSON database."""
    
    print("=" * 80)
    print("Testing CareerAnalysisAgent with JSON Database Integration")
    print("=" * 80)
    
    # Create agent
    agent = create_career_analysis_agent()
    
    # Process using latest major JSON file
    print("\n[Step 1] Loading latest major research data...")
    results = await agent.process_query()
    
    # Display results
    print("\n" + "=" * 80)
    print("Career Analysis Results")
    print("=" * 80)
    
    if not results:
        print("\n❌ No results generated. Check if majors_latest.json exists.")
        return
    
    for major_name, careers in results.items():
        print(f"\n{'=' * 80}")
        print(f"Major: {major_name}")
        print(f"{'=' * 80}")
        
        for career_title, career_data in careers.items():
            print(f"\n  Career: {career_title}")
            print(f"  {'-' * 76}")
            
            description = career_data.get('description', '')
            if description:
                print(f"  Description:")
                # Wrap text at 72 chars for readability
                words = description.split()
                line = "    "
                for word in words:
                    if len(line) + len(word) + 1 > 76:
                        print(line)
                        line = "    " + word
                    else:
                        line += " " + word if line.strip() else word
                if line.strip():
                    print(line)
            else:
                print(f"  Description: (LLM generation failed)")
            
            resources = career_data.get('resources', [])
            print(f"\n  Resources ({len(resources)} URLs):")
            if resources:
                for i, url in enumerate(resources, 1):
                    print(f"    {i}. {url}")
            else:
                print(f"    (No resources found)")
            
            print()
    
    print("\n" + "=" * 80)
    print("✅ Career analysis complete!")
    print("=" * 80)
    print("\nResults saved to:")
    db_dir = os.path.join(os.path.dirname(__file__), '..', 'backend', 'database')
    print(f"  - {os.path.join(db_dir, 'careers_latest.json')}")
    print(f"  - {os.path.join(db_dir, 'careers_<timestamp>.json')}")
    print("\nYou can inspect these files to see the full career analysis data structure.")


if __name__ == "__main__":
    asyncio.run(test_career_analysis())

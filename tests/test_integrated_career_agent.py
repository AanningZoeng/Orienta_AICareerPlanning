"""Test integrated CareerAnalysisAgent with both web resources and job database."""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# CRITICAL: Import Config FIRST
from backend.config import Config
from backend.agents.career_analysis_agent import create_career_analysis_agent


async def main():
    print("="*80)
    print("Testing Integrated CareerAnalysisAgent")
    print("="*80)
    
    # Create agent
    agent = create_career_analysis_agent()
    print(f"\n🔍 Database Diagnostics:")
    print(f"  DB path: {agent.db_path}")
    print(f"  DB exists: {agent.db_path.exists()}")
    
    # Check if scikit-learn is available
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        print(f"  scikit-learn: ✅ Installed")
    except ImportError:
        print(f"  scikit-learn: ❌ NOT installed (DB features disabled)")
    
    # If DB exists, check its content
    if agent.db_path.exists():
        import sqlite3
        try:
            conn = sqlite3.connect(agent.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM jobs')
            count = cursor.fetchone()[0]
            print(f"  DB records: {count} jobs")
            
            # Sample a few job titles
            cursor.execute('SELECT "Job Title" FROM jobs LIMIT 5')
            titles = [row[0] for row in cursor.fetchall()]
            print(f"  Sample titles: {', '.join(titles[:3])}")
            conn.close()
        except Exception as e:
            print(f"  DB error: {e}")
    else:
        print(f"  ⚠️  Database file not found!")
        print(f"  Expected location: {agent.db_path}")
        print(f"  📌 Tip: Place job_info.db in backend/agents/ directory")
    
    # Test with a sample career
    test_career = "Software Engineer"
    test_major = "Computer Science"
    
    print(f"\n\nAnalyzing career: {test_career} (for {test_major} graduates)")
    print("-"*80)
    
    result = await agent.analyze_career_simple(test_career, test_major)
    
    print("\n📊 RESULT STRUCTURE:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n📝 SUMMARY:")
    print(f"Description length: {len(result.get('description', ''))} chars")
    print(f"Resources count: {len(result.get('resources', []))} URLs")
    print(f"DB matches: {result.get('db_match_count', 0)}")
    print(f"Job examples: {len(result.get('job_examples', []))}")
    
    salary = result.get('salary', {})
    print(f"Salary range: ${salary.get('min', 0):,.0f} - ${salary.get('max', 0):,.0f} {salary.get('currency', 'USD')}")
    
    if result.get('job_examples'):
        print(f"\n💼 Sample Job Examples:")
        for i, job in enumerate(result['job_examples'][:3], 1):
            print(f"  {i}. {job.get('job_title')} at {job.get('company')}")
            print(f"     Salary: {job.get('salary_range')}")
    else:
        print(f"\n⚠️  No job examples found in database")
        if not agent.db_path.exists():
            print(f"   Reason: Database file not found at {agent.db_path}")
            print(f"   Solution: Create job_info.db with job data")
        elif result.get('db_match_count', 0) == 0:
            print(f"   Reason: No matching jobs found for '{test_career}'")
            print(f"   Solution: Add more job titles to database")
    
    print("\n✅ Integration test complete!")


if __name__ == "__main__":
    asyncio.run(main())

"""Test CareerAnalysisAgent database functionality (agent2 features)."""
import asyncio
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# CRITICAL: Import Config FIRST
from backend.config import Config
from backend.agents.career_analysis_agent import create_career_analysis_agent


async def main():
    print("\n" + "="*80)
    print("Testing CareerAnalysisAgent - Database Features (Agent2)")
    print("="*80)
    
    # Step 1: Check dependencies
    print("\n[Step 1] Checking Dependencies")
    print("-"*80)
    
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        print("✅ scikit-learn: Installed")
        sklearn_available = True
    except ImportError:
        print("❌ scikit-learn: NOT installed")
        print("   Install with: pip install scikit-learn")
        sklearn_available = False
    
    try:
        import sqlite3
        print("✅ sqlite3: Available")
    except ImportError:
        print("❌ sqlite3: NOT available")
        return
    
    # Step 2: Check database file
    print("\n[Step 2] Checking Database")
    print("-"*80)
    
    agent = create_career_analysis_agent()
    db_path = agent.db_path
    
    print(f"Expected DB path: {db_path}")
    print(f"DB exists: {db_path.exists()}")
    
    if not db_path.exists():
        print("\n⚠️  Database file not found!")
        print(f"\n📝 To create the database:")
        print(f"   1. Place job_info.db in: {db_path.parent}/")
        print(f"   2. Or specify custom path: create_career_analysis_agent(db_path='path/to/db')")
        print(f"\n💡 Expected SQL structure:")
        print(f"   CREATE TABLE jobs (")
        print(f"       \"Job Title\" TEXT,")
        print(f"       \"Company\" TEXT,")
        print(f"       \"Salary Range\" TEXT,")
        print(f"       \"Job Description\" TEXT")
        print(f"   );")
        
        # Ask if user wants to create a sample DB
        print(f"\n❓ Create a sample database for testing? (y/n): ", end='')
        
        # For automated testing, just show the message
        print("Skipped (run interactively to create)")
        return
    
    # Step 3: Analyze database content
    print("\n[Step 3] Analyzing Database Content")
    print("-"*80)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get total count
        cursor.execute('SELECT COUNT(*) FROM jobs')
        total_jobs = cursor.fetchone()[0]
        print(f"📊 Total jobs in database: {total_jobs}")
        
        # Get sample job titles
        cursor.execute('SELECT "Job Title" FROM jobs LIMIT 10')
        sample_titles = [row[0] for row in cursor.fetchall()]
        print(f"\n📋 Sample job titles:")
        for i, title in enumerate(sample_titles, 1):
            print(f"   {i}. {title}")
        
        # Get unique companies
        cursor.execute('SELECT COUNT(DISTINCT Company) FROM jobs')
        unique_companies = cursor.fetchone()[0]
        print(f"\n🏢 Unique companies: {unique_companies}")
        
    except Exception as e:
        print(f"❌ Database query error: {e}")
        conn.close()
        return
    
    conn.close()
    
    # Step 4: Test TF-IDF similarity matching
    if sklearn_available:
        print("\n[Step 4] Testing TF-IDF Similarity Matching")
        print("-"*80)
        
        test_jobs = [
            "Software Engineer",
            "Data Scientist", 
            "Product Manager",
            "Machine Learning Engineer"
        ]
        
        for job_title in test_jobs:
            matches = agent._vec_similarity(job_title, threshold=0.2)
            print(f"\n🔍 Query: '{job_title}'")
            print(f"   Matches: {len(matches)}")
            if matches:
                print(f"   Top 3: {', '.join(matches[:3])}")
    else:
        print("\n[Step 4] Skipped - scikit-learn not installed")
    
    # Step 5: Test salary parsing
    print("\n[Step 5] Testing Salary Parsing")
    print("-"*80)
    
    test_salaries = [
        "$100k - $150k",
        "$80,000 - $120,000",
        "100k-150k",
        "$50000-$80000"
    ]
    
    for salary_str in test_salaries:
        parsed = agent._parse_salary(salary_str)
        print(f"   '{salary_str}' → {parsed}")
    
    # Step 6: Test full database query
    print("\n[Step 6] Testing Full Database Query")
    print("-"*80)
    
    test_career = "Software Engineer"
    print(f"Querying: {test_career}")
    
    import asyncio
    loop = asyncio.get_event_loop()
    db_data = await loop.run_in_executor(None, agent._fetch_job_db_data, test_career)
    
    print(f"\n📊 Results:")
    print(f"   DB matches: {db_data.get('db_match_count', 0)}")
    print(f"   Salary min: ${db_data.get('salary', {}).get('min', 0):,.0f}")
    print(f"   Salary max: ${db_data.get('salary', {}).get('max', 0):,.0f}")
    print(f"   Job examples: {len(db_data.get('job_examples', []))}")
    
    if db_data.get('job_examples'):
        print(f"\n💼 Sample Job Examples:")
        for i, job in enumerate(db_data['job_examples'][:3], 1):
            print(f"\n   {i}. {job.get('job_title')}")
            print(f"      Company: {job.get('company')}")
            print(f"      Salary: {job.get('salary_range')}")
            desc = job.get('description', '')
            print(f"      Description: {desc[:100]}...")
    
    # Step 7: Test integrated analysis
    print("\n[Step 7] Testing Integrated Career Analysis")
    print("-"*80)
    
    result = await agent.analyze_career_simple(test_career, "Computer Science")
    
    print(f"\n✅ Analysis Complete:")
    print(f"   Description: {len(result.get('description', ''))} chars")
    print(f"   Resources: {len(result.get('resources', []))} URLs")
    print(f"   Salary: ${result.get('salary', {}).get('min', 0):,.0f} - ${result.get('salary', {}).get('max', 0):,.0f}")
    print(f"   Job examples: {len(result.get('job_examples', []))}")
    print(f"   DB matches: {result.get('db_match_count', 0)}")
    
    # Final summary
    print("\n" + "="*80)
    print("Test Summary")
    print("="*80)
    
    if not db_path.exists():
        print("❌ Database not found - DB features unavailable")
    elif not sklearn_available:
        print("⚠️  scikit-learn not installed - TF-IDF matching disabled")
    elif db_data.get('db_match_count', 0) == 0:
        print("⚠️  No matching jobs found - check database content")
    else:
        print("✅ All database features working correctly!")
    
    print("\n💡 Next Steps:")
    if not db_path.exists():
        print("   1. Create or copy job_info.db to backend/agents/")
    if not sklearn_available:
        print("   2. Install scikit-learn: pip install scikit-learn")
    print("   3. Run full integration test: python tests/test_integrated_career_agent.py")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

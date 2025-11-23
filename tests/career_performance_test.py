"""Performance Test for CareerAnalysisAgent

This script tests the performance of career_analysis_agent.py by:
1. Loading majors from majors_latest.json
2. For each major, calling the agent to generate 3 careers
3. Collecting career descriptions, resources, salary data, and job examples
4. Saving formatted results to careers_performance_test.json in the database folder
5. Measuring execution time and API calls made
"""

import asyncio
import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import Config FIRST to load .env before any other imports
from backend.config import Config
from backend.agents.career_analysis_agent import create_career_analysis_agent


class PerformanceMetrics:
    """Track performance metrics during test execution."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.major_count = 0
        self.career_count = 0
        self.api_calls = 0
        self.errors = 0
        self.major_times = {}
    
    def start(self):
        self.start_time = time.time()
    
    def end(self):
        self.end_time = time.time()
    
    def duration(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0
    
    def record_major(self, major_name, duration, career_count):
        self.major_count += 1
        self.career_count += career_count
        self.major_times[major_name] = duration
    
    def record_api_call(self):
        self.api_calls += 1
    
    def record_error(self):
        self.errors += 1
    
    def summary(self):
        """Return performance summary as dictionary."""
        return {
            "total_duration_seconds": round(self.duration(), 2),
            "majors_processed": self.major_count,
            "careers_generated": self.career_count,
            "average_time_per_major": round(self.duration() / self.major_count, 2) if self.major_count > 0 else 0,
            "average_time_per_career": round(self.duration() / self.career_count, 2) if self.career_count > 0 else 0,
            "api_calls_estimated": self.api_calls,
            "errors": self.errors,
            "major_processing_times": self.major_times
        }


async def load_majors_json(json_path=None):
    """Load majors data from JSON file.
    
    Args:
        json_path: Path to specific JSON file. If None, uses majors_latest.json
    
    Returns:
        Dictionary with majors data
    """
    try:
        if json_path is None:
            db_dir = Path(__file__).resolve().parent.parent / 'backend' / 'database'
            json_path = db_dir / 'majors_latest.json'
        else:
            json_path = Path(json_path)
        
        if not json_path.exists():
            print(f"[ERROR] JSON file not found: {json_path}")
            return None
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"[OK] Loaded majors data from {json_path.name}")
        return data
    
    except Exception as e:
        print(f"[ERROR] Failed to load JSON: {e}")
        return None


async def generate_careers_for_major(agent, major_name, major_desc, metrics):
    """Generate careers for a single major.
    
    Args:
        agent: CareerAnalysisAgent instance
        major_name: Name of the major
        major_desc: Description of the major (not used but available for context)
        metrics: PerformanceMetrics instance
    
    Returns:
        Dictionary of careers for this major
    """
    major_start = time.time()
    
    try:
        print(f"\n{'='*80}")
        print(f"Processing Major: {major_name}")
        print(f"{'='*80}")
        
        # Step 1: Identify 3 careers for this major
        print(f"[1/2] Identifying careers for {major_name}...")
        career_titles = await agent.identify_careers(major_name)
        metrics.record_api_call()  # One LLM call or search
        
        print(f"      Found {len(career_titles)} careers: {', '.join(career_titles)}")
        
        # Step 2: Analyze each career
        careers_data = {}
        for i, career_title in enumerate(career_titles, 1):
            print(f"[2/2] Analyzing career {i}/{len(career_titles)}: {career_title}")
            
            try:
                # analyze_career_simple generates:
                # - description (1 LLM call)
                # - resources (1 LLM call for queries + 3 web searches)
                # - salary + job_examples (1 DB query)
                career_data = await agent.analyze_career_simple(career_title, major_name)
                metrics.record_api_call()  # Description LLM call
                metrics.record_api_call()  # Resource queries LLM call
                
                careers_data[career_title] = career_data
                
                # Print summary
                desc_preview = career_data.get('description', '')[:80] + "..." if len(career_data.get('description', '')) > 80 else career_data.get('description', '')
                print(f"      [+] Description: {desc_preview}")
                print(f"      [+] Resources: {len(career_data.get('resources', []))} URLs")
                
                salary = career_data.get('salary', {})
                if salary.get('min', 0) > 0:
                    print(f"      [+] Salary: ${salary.get('min', 0):,.0f} - ${salary.get('max', 0):,.0f} {salary.get('currency', 'USD')}")
                else:
                    print(f"      [+] Salary: No data available")
                
                print(f"      [+] Job Examples: {career_data.get('db_match_count', 0)} matches")
                
            except Exception as e:
                print(f"      [ERROR] Error analyzing {career_title}: {e}")
                metrics.record_error()
                careers_data[career_title] = {
                    'description': '',
                    'resources': [],
                    'salary': {'min': 0, 'max': 0, 'currency': 'USD'},
                    'job_examples': [],
                    'db_match_count': 0,
                    'error': str(e)
                }
        
        major_duration = time.time() - major_start
        metrics.record_major(major_name, round(major_duration, 2), len(career_titles))
        
        print(f"\n[OK] Completed {major_name} in {major_duration:.2f} seconds")
        
        return careers_data
    
    except Exception as e:
        print(f"[ERROR] Error processing major {major_name}: {e}")
        metrics.record_error()
        return {}


async def save_results(results, user_query, source_timestamp, metrics):
    """Save performance test results to JSON file in database folder.
    
    Args:
        results: Dictionary of {major: {career: {data}}}
        user_query: Original user query
        source_timestamp: Timestamp from source majors JSON
        metrics: PerformanceMetrics instance
    """
    try:
        db_dir = Path(__file__).resolve().parent.parent / 'backend' / 'database'
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Create output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"careers_performance_test_{timestamp}.json"
        output_path = db_dir / output_filename
        
        # Format output data
        output_data = {
            "test_metadata": {
                "test_name": "Career Analysis Agent Performance Test",
                "timestamp": datetime.now().isoformat(),
                "source_timestamp": source_timestamp,
                "user_query": user_query,
                "performance_metrics": metrics.summary()
            },
            "careers": results
        }
        
        # Save to timestamped file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        # Also save as careers_performance_latest.json for easy access
        latest_path = db_dir / "careers_performance_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*80}")
        print(f"[OK] Results saved successfully!")
        print(f"{'='*80}")
        print(f"Output files:")
        print(f"  1. {output_path}")
        print(f"  2. {latest_path}")
        
        return output_path
    
    except Exception as e:
        print(f"[ERROR] Failed to save results: {e}")
        return None


async def run_performance_test(json_path=None):
    """Main performance test function.
    
    Args:
        json_path: Optional path to specific majors JSON file
    """
    print("\n" + "="*80)
    print("CAREER ANALYSIS AGENT - PERFORMANCE TEST")
    print("="*80)
    
    # Initialize metrics
    metrics = PerformanceMetrics()
    metrics.start()
    
    # Load majors data
    print("\n[Step 1] Loading majors data...")
    major_data = await load_majors_json(json_path)
    
    if not major_data:
        print("[ERROR] Cannot proceed without majors data")
        return
    
    majors = major_data.get('majors', {})
    user_query = major_data.get('user_query', '')
    source_timestamp = major_data.get('timestamp', '')
    
    print(f"         Found {len(majors)} majors to process")
    print(f"         User query: {user_query}")
    
    # Create agent
    print("\n[Step 2] Initializing CareerAnalysisAgent...")
    agent = create_career_analysis_agent()
    print("         [OK] Agent initialized")
    
    # Database diagnostics
    print("\n         Database Diagnostics:")
    print(f"         - DB path: {agent.db_path}")
    print(f"         - DB exists: {agent.db_path.exists()}")
    
    # Check if scikit-learn is available
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        print(f"         - scikit-learn: [OK] Installed")
    except ImportError:
        print(f"         - scikit-learn: [ERROR] NOT installed (DB features disabled)")
    
    # If DB exists, check its content
    if agent.db_path.exists():
        import sqlite3
        try:
            conn = sqlite3.connect(agent.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM jobs')
            count = cursor.fetchone()[0]
            print(f"         - DB records: {count} jobs")
            
            # Sample a few job titles
            cursor.execute('SELECT "Job Title" FROM jobs LIMIT 5')
            titles = [row[0] for row in cursor.fetchall()]
            print(f"         - Sample titles: {', '.join(titles[:3])}")
            conn.close()
        except Exception as e:
            print(f"         - DB error: {e}")
    else:
        print(f"         - [WARNING] Database file not found!")
        print(f"         - Expected location: {agent.db_path}")
        print(f"         - Tip: Salary and job examples will not be available")
    
    # Process each major
    print("\n[Step 3] Processing majors and generating careers...")
    results = {}
    
    for major_name, major_info in majors.items():
        major_desc = major_info.get('description', '')
        careers = await generate_careers_for_major(agent, major_name, major_desc, metrics)
        results[major_name] = careers
    
    # End timing
    metrics.end()
    
    # Save results
    print("\n[Step 4] Saving results to database...")
    output_path = await save_results(results, user_query, source_timestamp, metrics)
    
    # Print performance summary
    print("\n" + "="*80)
    print("PERFORMANCE SUMMARY")
    print("="*80)
    perf = metrics.summary()
    print(f"Total Duration:           {perf['total_duration_seconds']} seconds")
    print(f"Majors Processed:         {perf['majors_processed']}")
    print(f"Careers Generated:        {perf['careers_generated']}")
    print(f"Avg Time per Major:       {perf['average_time_per_major']} seconds")
    print(f"Avg Time per Career:      {perf['average_time_per_career']} seconds")
    print(f"Estimated API Calls:      {perf['api_calls_estimated']}")
    print(f"Errors:                   {perf['errors']}")
    
    print(f"\nProcessing Times by Major:")
    for major_name, duration in perf['major_processing_times'].items():
        print(f"  - {major_name}: {duration}s")
    
    print("\n" + "="*80)
    print("[OK] PERFORMANCE TEST COMPLETE")
    print("="*80)
    
    if output_path:
        print(f"\nView detailed results at:")
        print(f"  {output_path}")


if __name__ == "__main__":
    # Run the performance test
    # To test a specific file, pass the path as argument:
    # python career_performance_test.py path/to/majors.json
    
    json_path = None
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    
    asyncio.run(run_performance_test(json_path))

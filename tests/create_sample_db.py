"""Create a sample job_info.db for testing database features."""
import sqlite3
import os
from pathlib import Path

# Database will be created in backend/agents/
db_path = Path(__file__).parent.parent / "backend" / "agents" / "job_info.db"

print("="*80)
print("Creating Sample Job Database")
print("="*80)
print(f"\nTarget location: {db_path}")

# Sample job data
sample_jobs = [
    # Software Engineering
    ("Software Engineer", "Google", "$120k - $180k", "Design and develop scalable software systems. Work with cross-functional teams to deliver high-quality products."),
    ("Software Engineer", "Microsoft", "$110k - $170k", "Build cloud-based solutions and services. Collaborate with product managers and designers."),
    ("Senior Software Engineer", "Amazon", "$150k - $220k", "Lead technical design and architecture decisions. Mentor junior engineers."),
    ("Software Developer", "Apple", "$130k - $190k", "Develop innovative applications for iOS and macOS platforms."),
    ("Backend Engineer", "Meta", "$140k - $200k", "Build scalable backend services and APIs. Work with distributed systems."),
    
    # Data Science
    ("Data Scientist", "Google", "$130k - $190k", "Apply machine learning to solve complex business problems. Analyze large datasets."),
    ("Data Scientist", "Netflix", "$140k - $200k", "Build recommendation systems and personalization algorithms."),
    ("Senior Data Scientist", "Uber", "$160k - $230k", "Lead data-driven decision making. Develop predictive models."),
    ("Machine Learning Engineer", "OpenAI", "$150k - $250k", "Research and develop advanced ML models. Work on cutting-edge AI systems."),
    ("Data Analyst", "Airbnb", "$90k - $140k", "Analyze user behavior and business metrics. Create data visualizations."),
    
    # Product Management
    ("Product Manager", "Google", "$140k - $200k", "Define product strategy and roadmap. Work with engineering and design teams."),
    ("Senior Product Manager", "Amazon", "$160k - $240k", "Lead product development from concept to launch. Drive cross-functional initiatives."),
    ("Product Manager", "Stripe", "$150k - $210k", "Build payment infrastructure products. Understand developer needs."),
    ("Associate Product Manager", "Facebook", "$110k - $160k", "Support product development initiatives. Conduct user research."),
    
    # Web Development
    ("Frontend Engineer", "Shopify", "$100k - $150k", "Build modern web interfaces using React and TypeScript."),
    ("Full Stack Developer", "Atlassian", "$110k - $160k", "Develop end-to-end web applications. Work with Node.js and React."),
    ("Frontend Developer", "Adobe", "$105k - $155k", "Create beautiful user interfaces. Work with design systems."),
    
    # DevOps/Infrastructure
    ("DevOps Engineer", "Google", "$120k - $180k", "Manage cloud infrastructure and CI/CD pipelines. Ensure system reliability."),
    ("Site Reliability Engineer", "Meta", "$140k - $200k", "Build and maintain large-scale distributed systems. On-call support."),
    ("Cloud Engineer", "AWS", "$110k - $170k", "Design and implement cloud solutions. Work with AWS services."),
    
    # Security
    ("Security Engineer", "Google", "$130k - $190k", "Protect systems and data from security threats. Conduct security audits."),
    ("Cybersecurity Analyst", "Microsoft", "$100k - $150k", "Monitor and respond to security incidents. Implement security controls."),
    
    # Mobile Development
    ("iOS Engineer", "Apple", "$120k - $180k", "Develop native iOS applications using Swift. Focus on user experience."),
    ("Android Engineer", "Google", "$115k - $175k", "Build Android applications using Kotlin. Work with Material Design."),
    ("Mobile Developer", "Uber", "$110k - $170k", "Develop cross-platform mobile apps. Use React Native or Flutter."),
    
    # Research
    ("Research Scientist", "DeepMind", "$150k - $250k", "Conduct cutting-edge AI research. Publish papers in top conferences."),
    ("Research Engineer", "OpenAI", "$140k - $220k", "Implement research ideas into production systems."),
    
    # Consulting
    ("Software Consultant", "Accenture", "$90k - $140k", "Advise clients on technology solutions. Implement custom software."),
    ("Technical Consultant", "Deloitte", "$95k - $145k", "Provide technical expertise to enterprise clients."),
    
    # Startups
    ("Software Engineer", "Early-stage Startup", "$80k - $130k + equity", "Wear multiple hats. Build products from scratch in fast-paced environment."),
    ("Founding Engineer", "YC Startup", "$90k - $150k + equity", "First engineering hire. Define technical architecture and culture."),
]

# Create database
try:
    # Remove existing database if it exists
    if db_path.exists():
        print(f"\n⚠️  Database already exists. Overwrite? (y/n): ", end='')
        # For automated script, just overwrite
        print("yes (auto)")
        os.remove(db_path)
    
    # Create connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table
    print("\n[1/3] Creating table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            "Job Title" TEXT,
            Company TEXT,
            "Salary Range" TEXT,
            "Job Description" TEXT
        )
    ''')
    
    # Insert sample data
    print(f"[2/3] Inserting {len(sample_jobs)} jobs...")
    cursor.executemany(
        'INSERT INTO jobs VALUES (?, ?, ?, ?)',
        sample_jobs
    )
    
    # Commit changes
    conn.commit()
    
    # Verify
    print("[3/3] Verifying...")
    cursor.execute('SELECT COUNT(*) FROM jobs')
    count = cursor.fetchone()[0]
    print(f"✅ Successfully created database with {count} jobs")
    
    # Show some statistics
    cursor.execute('SELECT COUNT(DISTINCT "Job Title") FROM jobs')
    unique_titles = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT Company) FROM jobs')
    unique_companies = cursor.fetchone()[0]
    
    print(f"\n📊 Database Statistics:")
    print(f"   Total jobs: {count}")
    print(f"   Unique job titles: {unique_titles}")
    print(f"   Unique companies: {unique_companies}")
    
    # Sample job titles
    cursor.execute('SELECT DISTINCT "Job Title" FROM jobs LIMIT 10')
    titles = [row[0] for row in cursor.fetchall()]
    print(f"\n📋 Sample job titles:")
    for title in titles:
        print(f"   - {title}")
    
    conn.close()
    
    print(f"\n✅ Database created successfully!")
    print(f"   Location: {db_path}")
    print(f"\n💡 Next steps:")
    print(f"   1. Run: python tests/test_agent2_database.py")
    print(f"   2. Test integration: python tests/test_integrated_career_agent.py")
    
except Exception as e:
    print(f"\n❌ Error creating database: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80 + "\n")

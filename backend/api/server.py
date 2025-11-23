"""
REST API Server for Career Planning Application.
Provides endpoints for frontend to interact with the multi-agent system.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import os
import sys

# Add parent directory to path so we can import from project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.config import Config
from backend.agents.orchestrator_agent import create_orchestrator

# Initialize Flask app
app = Flask(__name__, 
            static_folder='../../frontend',
            static_url_path='')
CORS(app)  # Enable CORS for frontend access

# Global orchestrator instance
orchestrator = None


def init_orchestrator():
    """Initialize the orchestrator agent."""
    global orchestrator
    
    try:
        # Validate configuration
        Config.validate()
        
        # Create orchestrator with configured LLM
        orchestrator = create_orchestrator(
            llm_provider=Config.LLM_PROVIDER,
            model_name=Config.MODEL_NAME
        )
        
        print(f"[OK] Orchestrator initialized with {Config.LLM_PROVIDER}/{Config.MODEL_NAME}")
        
    except ValueError as e:
        print(f"[WARNING] Configuration error: {e}")
        print("[WARNING] API will run with mock data only (no LLM calls)")
        # Set orchestrator to None - we'll handle requests with mock data
        orchestrator = None

async def process_query_async(user_query: str) -> dict:
    """Process user query through the orchestrator."""
    if orchestrator:
        result = await orchestrator.process_query(user_query)
        # Transform new format (dict keyed by major) to frontend-compatible format
        majors_list = []
        for major_name, major_data in result.items():
            majors_list.append({
                "id": major_name.lower().replace(" ", "_"),
                "name": major_name,
                "description": major_data.get("description", ""),
                "resources": major_data.get("resources", []),
                "careers": [],  # Will be populated by career agent if orchestrator includes it
                "future_paths": []
            })
        return {
            "user_query": user_query,
            "majors": majors_list
        }
    else:
        # Return mock data if orchestrator not initialized
        return {
            "user_query": user_query,
            "majors": [
                {
                    "id": "computer_science",
                    "name": "Computer Science",
                    "description": "Study of computers and computational systems",
                    "resources": [],
                    "careers": [
                        {
                            "id": "software_engineer",
                            "title": "Software Engineer",
                            "salary_range": "$80,000 - $180,000",
                            "future_paths": []
                        }
                    ]
                }
            ]
        }


@app.route('/')
def index():
    """Serve the main frontend page."""
    return app.send_static_file('index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "orchestrator_ready": orchestrator is not None,
        "llm_provider": Config.LLM_PROVIDER if orchestrator else "none"
    })


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Main endpoint: Analyze user query and return career path recommendations.
    
    Request body:
        {
            "query": "User's interests and career goals"
        }
    
    Response:
        {
            "majors": [
                {
                    "id": "...",
                    "name": "...",
                    "description": "...",
                    "careers": [
                        {
                            "id": "...",
                            "title": "...",
                            "future_paths": [...]
                        }
                    ]
                }
            ]
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({"error": "Missing 'query' field in request"}), 400
        
        user_query = data['query']
        
        # Process query through orchestrator
        result = asyncio.run(process_query_async(user_query))
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/research-majors', methods=['POST'])
def research_majors():
    """
    Research majors based on user query.
    Calls MajorResearchAgent directly.
    
    Request body:
        {
            "query": "User's interests and goals"
        }
    
    Response:
        {
            "majors": {
                "Computer Science": {
                    "description": "...",
                    "resources": ["url1", "url2", ...]
                },
                ...
            }
        }
    """
    try:
        from backend.agents.major_research_agent import create_major_research_agent
        
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Missing 'query' field"}), 400
        
        user_query = data['query']
        
        # Create and run MajorResearchAgent
        agent = create_major_research_agent()
        result = asyncio.run(agent.process_query(user_query))
        
        return jsonify({"majors": result})
        
    except Exception as e:
        print(f"Error researching majors: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/major-research', methods=['POST'])
def major_research():
    """
    Frontend-friendly endpoint for Major Research Agent.
    Returns list of majors in a format ready for the bubble tree.
    """
    try:
        from backend.agents.major_research_agent import create_major_research_agent
        
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query cannot be empty'
            }), 400
        
        # Create and run agent
        agent = create_major_research_agent(
            llm_provider=Config.LLM_PROVIDER,
            model_name=Config.MODEL_NAME
        )
        
        result = asyncio.run(agent.process_query(query))
        
        # Transform to frontend format
        majors_list = []
        for major_name, major_data in result.items():
            # 处理resources：将字符串URL转换为对象格式
            resources = major_data.get("resources", [])
            formatted_resources = []
            
            for resource in resources:
                if isinstance(resource, str):
                    # 从URL提取标题
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(resource)
                        hostname = parsed.hostname or ''
                        hostname = hostname.replace('www.', '').replace('m.', '')
                        
                        # 根据域名判断类型
                        if 'youtube' in hostname or 'youtu.be' in hostname:
                            resource_type = 'video'
                            title = f"YouTube: {hostname}"
                        elif 'medium' in hostname or 'blog' in hostname:
                            resource_type = 'article'
                            title = f"文章: {hostname}"
                        elif 'coursera' in hostname or 'udemy' in hostname or 'edu' in hostname:
                            resource_type = 'course'
                            title = f"课程: {hostname}"
                        elif 'reddit' in hostname or 'forum' in hostname:
                            resource_type = 'website'
                            title = f"论坛: {hostname}"
                        else:
                            resource_type = 'website'
                            title = hostname
                        
                        formatted_resources.append({
                            "url": resource,
                            "title": title,
                            "type": resource_type
                        })
                    except Exception as e:
                        # 如果解析失败，使用原始URL
                        formatted_resources.append({
                            "url": resource,
                            "title": resource,
                            "type": "website"
                        })
                else:
                    # 已经是对象格式
                    formatted_resources.append(resource)
            
            majors_list.append({
                "name": major_name,
                "description": major_data.get("description", ""),
                "core_courses": major_data.get("core_courses", []),
                "resources": formatted_resources,
                "universities": major_data.get("universities", [])
            })
        
        return jsonify({
            'success': True,
            'majors': majors_list
        })
        
    except Exception as e:
        print(f"[ERROR] Major research failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analyze-careers', methods=['POST'])
def analyze_careers():
    """
    Analyze careers for a specific major.
    Calls CareerAnalysisAgent directly.
    
    Request body:
        {
            "major_name": "Computer Science"
        }
    
    Response:
        {
            "careers": {
                "Software Engineer": {
                    "description": "...",
                    "resources": ["url1", "url2", ...]
                },
                ...
            }
        }
    """
    try:
        from backend.agents.career_analysis_agent import create_career_analysis_agent
        
        data = request.get_json()
        if not data or 'major_name' not in data:
            return jsonify({"error": "Missing 'major_name' field"}), 400
        
        major_name = data['major_name']
        
        # Create and run CareerAnalysisAgent
        agent = create_career_analysis_agent()
        
        # Load latest major data and filter for this major
        import json
        db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database')
        majors_path = os.path.join(db_dir, 'majors_latest.json')
        
        if not os.path.exists(majors_path):
            return jsonify({"error": "No major data found. Please run major research first."}), 404
        
        # For now, use the existing process_query which processes all majors
        # Then filter for the requested major
        result = asyncio.run(agent.process_query())
        
        if major_name in result:
            return jsonify({"careers": result[major_name]})
        else:
            # Major not found, return empty
            return jsonify({"careers": {}})
        
    except Exception as e:
        print(f"Error analyzing careers: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/career-analysis', methods=['POST'])
def career_analysis():
    """
    Frontend-friendly endpoint for Career Analysis Agent.
    Returns list of careers in a format ready for the bubble tree.
    """
    try:
        from backend.agents.career_analysis_agent import create_career_analysis_agent
        
        data = request.get_json()
        major_name = data.get('major_name', '')
        
        if not major_name:
            return jsonify({
                'success': False,
                'error': 'Major name cannot be empty'
            }), 400
        
        # Create agent
        agent = create_career_analysis_agent(
            llm_provider=Config.LLM_PROVIDER,
            model_name=Config.MODEL_NAME
        )
        
        # Process all majors (agent reads from majors_latest.json)
        result = asyncio.run(agent.process_query())
        
        # Extract careers for requested major
        if major_name not in result:
            return jsonify({
                'success': False,
                'error': f'No careers found for major: {major_name}'
            }), 404
        
        careers_data = result[major_name]
        
        # Transform to frontend format
        careers_list = []
        for career_title, career_info in careers_data.items():
            careers_list.append({
                "title": career_title,
                "description": career_info.get("description", ""),
                "salary": career_info.get("salary", {}),
                "resources": career_info.get("resources", []),
                "job_examples": career_info.get("job_examples", []),
                "db_match_count": career_info.get("db_match_count", 0)
            })
        
        return jsonify({
            'success': True,
            'careers': careers_list
        })
        
    except Exception as e:
        print(f"[ERROR] Career analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/future-path-analysis', methods=['POST'])
def future_path_analysis():
    """
    Frontend-friendly endpoint for Future Path Agent.
    Returns future career progression paths for a specific career.
    
    Request body:
        {
            "career_title": "Software Engineer",
            "years": 5  // optional, default 5
        }
    
    Response:
        {
            "success": true,
            "future_paths": [
                {
                    "id": "...",
                    "career": "Software Engineer",
                    "timeframe": "5 years",
                    "statistics": {...},
                    "common_progressions": [...],
                    "insights": [...]
                }
            ]
        }
    """
    try:
        from backend.agents.future_path_agent import create_future_path_agent
        
        data = request.get_json()
        career_title = data.get('career_title', '')
        years = data.get('years', 5)
        
        if not career_title:
            return jsonify({
                'success': False,
                'error': 'Career title cannot be empty'
            }), 400
        
        # Create agent
        agent = create_future_path_agent(
            llm_provider=Config.LLM_PROVIDER,
            model_name=Config.MODEL_NAME
        )
        
        # Analyze progression for this career
        result = asyncio.run(agent.analyze_progression(career_title, years))
        
        return jsonify({
            'success': True,
            'future_path': result
        })
        
    except Exception as e:
        print(f"[ERROR] Future path analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/detail/major/<major_id>', methods=['GET'])
def get_major_detail(major_id):
    """
    Get detailed information about a specific major.
    Used when user clicks on a major bubble.
    """
    # In a real implementation, this would fetch from a database or cache
    # For now, return structure that frontend expects
    return jsonify({
        "id": major_id,
        "name": major_id.replace("_", " ").title(),
        "description": "Detailed major description...",
        "requirements": ["Requirement 1", "Requirement 2"],
        "universities": [
            {"name": "University 1", "url": "https://university1.edu"}
        ],
        "video_url": "https://youtube.com/watch?v=example"
    })


@app.route('/api/detail/career/<career_id>', methods=['GET'])
def get_career_detail(career_id):
    """
    Get detailed information about a specific career.
    Used when user clicks on a career bubble.
    """
    return jsonify({
        "id": career_id,
        "title": career_id.replace("_", " ").title(),
        "salary_range": "$50,000 - $100,000",
        "benefits": ["Benefit 1", "Benefit 2"],
        "work_intensity": "Medium",
        "professional_resources": {
            "videos": [],
            "blogs": [],
            "interviews": []
        }
    })


@app.route('/api/detail/future/<future_id>', methods=['GET'])
def get_future_detail(future_id):
    """
    Get detailed future path information.
    Used when user clicks on a future path bubble.
    """
    return jsonify({
        "id": future_id,
        "career": future_id.replace("_future", "").replace("_", " ").title(),
        "statistics": {
            "promoted": {"percentage": 45, "description": "..."},
            "same_role": {"percentage": 30, "description": "..."},
            "changed_company": {"percentage": 15, "description": "..."}
        },
        "common_progressions": [
            "Senior Role (35%)",
            "Management (25%)"
        ]
    })


def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("AI Career Path Planning API Server")
    print("="*60 + "\n")
    
    # Initialize orchestrator
    init_orchestrator()
    
    # Start Flask server
    print(f"\n[START] Starting server on {Config.API_HOST}:{Config.API_PORT}")
    print(f"[INFO] API documentation:")
    print(f"   POST /api/analyze - Analyze career interests (full pipeline)")
    print(f"   POST /api/research-majors - Research majors only")
    print(f"   POST /api/major-research - Frontend major research endpoint")
    print(f"   POST /api/analyze-careers - Analyze careers for a major")
    print(f"   POST /api/career-analysis - Frontend career analysis endpoint")
    print(f"   POST /api/future-path-analysis - Frontend future path analysis endpoint")
    print(f"   GET  /api/health - Health check")
    print(f"   GET  /api/detail/major/<id> - Get major details")
    print(f"   GET  /api/detail/career/<id> - Get career details")
    print(f"   GET  /api/detail/future/<id> - Get future path details")
    print(f"\n{'='*60}\n")
    
    app.run(
        host=Config.API_HOST,
        port=Config.API_PORT,
        debug=Config.DEBUG
    )


if __name__ == '__main__':
    main()

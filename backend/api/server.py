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
app = Flask(__name__)
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
        return await orchestrator.process_query(user_query)
    else:
        # Return mock data if orchestrator not initialized
        return {
            "user_query": user_query,
            "majors": [
                {
                    "id": "computer_science",
                    "name": "Computer Science",
                    "description": "Study of computers and computational systems",
                    "careers": [
                        {
                            "id": "software_engineer",
                            "title": "Software Engineer",
                            "salary_range": "$80,000 - $180,000",
                            "future_paths": [
                                {
                                    "career": "Software Engineer",
                                    "statistics": {
                                        "promoted": {"percentage": 45},
                                        "same_role": {"percentage": 30}
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }


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
    print(f"   POST /api/analyze - Analyze career interests")
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

"""
Orchestrator Agent - Coordinates the multi-agent workflow using SpoonOS Graph System.
"""
import asyncio
from typing import Dict, Any, TypedDict, Optional, Annotated, List
import json
import os
import sys
from datetime import datetime
import uuid
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# CRITICAL: Import Config and backend agents FIRST before SpoonAI
from backend.config import Config
from backend.agents.major_research_agent import create_major_research_agent
from backend.agents.career_analysis_agent import create_career_analysis_agent
from backend.agents.future_path_agent import create_future_path_agent

# Import SpoonAI graph modules after backend imports
from spoon_ai.graph import StateGraph, END
from spoon_ai.graph.builder import (
    DeclarativeGraphBuilder,
    GraphTemplate,
    NodeSpec,
    EdgeSpec,
    ParallelGroupSpec,
    ParallelGroupConfig
)
from spoon_ai.graph.config import GraphConfig


class CareerPlanningState(TypedDict):
    """State schema for the career planning workflow."""
    user_query: str
    majors: List[Dict[str, Any]]
    careers: Dict[str, List[Dict[str, Any]]]  # major_id -> list of careers
    future_paths: Dict[str, List[Dict[str, Any]]]  # career_id -> list of future paths
    result: Dict[str, Any]
    error: Optional[str]


class OrchestratorAgent:
    """
    Master agent that orchestrates the multi-agent career planning workflow.
    Uses SpoonOS StateGraph for parallel execution and intelligent routing.
    """
    
    def __init__(self, llm_provider: str = None, model_name: str = None):
        """
        Initialize the orchestrator with agent instances.
        
        Args:
            llm_provider: LLM provider to use (openai, anthropic, gemini)
            model_name: Model name to use
        """
        # Use provided values or fall back to Config
        self.llm_provider = llm_provider or Config.LLM_PROVIDER
        self.model_name = model_name or Config.MODEL_NAME

        # Create agent instances using resolved provider/model
        self.major_agent = create_major_research_agent(self.llm_provider, self.model_name)
        self.career_agent = create_career_analysis_agent(self.llm_provider, self.model_name)
        self.future_agent = create_future_path_agent(self.llm_provider, self.model_name)
        
        # Build the graph workflow
        self.graph = self._build_graph()
    
    async def research_majors_node(
        self, 
        state: CareerPlanningState, 
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Graph node: Research university majors based on user query.
        """
        print(f"[Orchestrator] Starting major research for query: {state['user_query'][:50]}...")
        
        try:
            result = await self.major_agent.process_query(state["user_query"])
            majors = result.get("recommended_majors", [])
            
            print(f"[Orchestrator] Found {len(majors)} majors")
            
            return {
                "majors": majors,
                "error": None
            }
        except Exception as e:
            print(f"[Orchestrator] Error in major research: {str(e)}")
            return {
                "majors": [],
                "error": f"Major research failed: {str(e)}"
            }
    
    async def analyze_careers_node(
        self, 
        state: CareerPlanningState, 
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Graph node: Analyze careers for each major (parallel execution for each major).
        """
        majors = state.get("majors", [])
        print(f"[Orchestrator] Analyzing careers for {len(majors)} majors...")
        
        careers_by_major = {}
        
        try:
            # Analyze careers for each major (could be parallelized further)
            for major in majors:
                major_name = major["name"]
                major_id = major["id"]
                
                print(f"[Orchestrator]   - Analyzing careers for {major_name}")
                
                career_result = await self.career_agent.process_major(major_name)
                careers_by_major[major_id] = career_result.get("careers", [])
            
            print(f"[Orchestrator] Career analysis complete")
            
            return {
                "careers": careers_by_major,
                "error": None
            }
        except Exception as e:
            print(f"[Orchestrator] Error in career analysis: {str(e)}")
            return {
                "careers": {},
                "error": f"Career analysis failed: {str(e)}"
            }
    
    async def project_future_paths_node(
        self, 
        state: CareerPlanningState, 
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Graph node: Project future paths for all careers.
        """
        careers = state.get("careers", {})
        print(f"[Orchestrator] Projecting future paths...")
        
        future_paths_by_career = {}
        
        try:
            # Process all careers across all majors
            for major_id, career_list in careers.items():
                for career in career_list:
                    career_id = career["id"]
                    career_title = career["title"]
                    
                    print(f"[Orchestrator]   - Projecting future for {career_title}")
                    
                    future_data = await self.future_agent.analyze_progression(career_title)
                    
                    if future_data:
                        future_paths_by_career[career_id] = [future_data]
            
            print(f"[Orchestrator] Future path projection complete")
            
            return {
                "future_paths": future_paths_by_career,
                "error": None
            }
        except Exception as e:
            print(f"[Orchestrator] Error in future path projection: {str(e)}")
            return {
                "future_paths": {},
                "error": f"Future path projection failed: {str(e)}"
            }
    
    async def compile_results_node(
        self, 
        state: CareerPlanningState, 
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Graph node: Compile final results into structured format.
        """
        print(f"[Orchestrator] Compiling final results...")
        
        majors = state.get("majors", [])
        careers = state.get("careers", {})
        future_paths = state.get("future_paths", {})
        
        # Build comprehensive result structure
        result = {
            "user_query": state["user_query"],
            "majors": []
        }
        
        for major in majors:
            major_id = major["id"]
            major_careers = careers.get(major_id, [])
            
            # Add future paths to each career
            for career in major_careers:
                career_id = career["id"]
                career["future_paths"] = future_paths.get(career_id, [])
            
            result["majors"].append({
                **major,
                "careers": major_careers
            })
        
        print(f"[Orchestrator] Results compiled successfully")
        
        return {
            "result": result,
            "error": None
        }
    
    def _build_graph(self) -> StateGraph:
        """
        Build the StateGraph workflow for career planning.
        Uses declarative graph building pattern from SpoonOS.
        """
        print("[Orchestrator] Building graph workflow...")
        
        # Define nodes
        nodes = [
            NodeSpec("research_majors", self.research_majors_node),
            NodeSpec("analyze_careers", self.analyze_careers_node),
            NodeSpec("project_future_paths", self.project_future_paths_node),
            NodeSpec("compile_results", self.compile_results_node),
        ]
        
        # Define edges (workflow flow)
        edges = [
            EdgeSpec("research_majors", "analyze_careers"),
            EdgeSpec("analyze_careers", "project_future_paths"),
            EdgeSpec("project_future_paths", "compile_results"),
            EdgeSpec("compile_results", END),
        ]
        
        # Configure graph
        config = GraphConfig(max_iterations=100)
        
        # Create template
        template = GraphTemplate(
            entry_point="research_majors",
            nodes=nodes,
            edges=edges,
            parallel_groups=[],  # Could add parallel groups for scaling
            config=config
        )
        
        # Build graph
        builder = DeclarativeGraphBuilder(CareerPlanningState)
        graph = builder.build(template)
        
        print("[Orchestrator] Graph workflow built successfully")
        
        return graph
    
    async def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Main entry point: Process user query through the entire workflow.
        
        Args:
            user_query: User's career interests and goals
            
        Returns:
            Comprehensive career planning results with majors, careers, and future paths
        """
        print(f"\n{'='*60}")
        print(f"[Orchestrator] Starting career planning workflow")
        print(f"[Orchestrator] Query: {user_query}")
        print(f"{'='*60}\n")
        
        # Initial state
        initial_state: CareerPlanningState = {
            "user_query": user_query,
            "majors": [],
            "careers": {},
            "future_paths": {},
            "result": {},
            "error": None
        }
        
        try:
            # Compile and execute the graph
            compiled_graph = self.graph.compile()
            final_state = await compiled_graph.invoke(initial_state)

            if final_state.get("error"):
                print(f"\n[Orchestrator] Workflow completed with errors: {final_state['error']}")
            else:
                print(f"\n[Orchestrator] Workflow completed successfully!")

            # Persist the full state/result as JSON memory
            try:
                self._save_memory(final_state)
            except Exception as e:
                print(f"⚠️ Failed to save memory JSON: {e}")

            print(f"{'='*60}\n")

            return final_state.get("result", {})

        except Exception as e:
            print(f"\n[Orchestrator] Workflow failed: {str(e)}")
            print(f"{'='*60}\n")

            # Attempt to save partial state including the error
            try:
                error_state = {**initial_state, "error": str(e)}
                self._save_memory(error_state)
            except Exception:
                pass

            return {
                "error": f"Workflow execution failed: {str(e)}",
                "user_query": user_query,
                "majors": []
            }

    def _save_memory(self, state: Dict[str, Any]) -> None:
        """Save the provided workflow state to a JSON file under backend/data.

        Writes two files:
         - backend/data/memory_{timestamp}_{uuid}.json  (historical)
         - backend/data/latest_memory.json             (overwritten each run)
        """
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'data')
        # Normalize path
        base_dir = os.path.abspath(base_dir)
        os.makedirs(base_dir, exist_ok=True)

        ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        nid = uuid.uuid4().hex[:8]
        hist_path = os.path.join(base_dir, f'memory_{ts}_{nid}.json')
        latest_path = os.path.join(base_dir, 'latest_memory.json')

        # Ensure JSON serializable: attempt to convert non-serializable objects
        def _safe(obj):
            try:
                json.dumps(obj)
                return obj
            except Exception:
                return str(obj)

        safe_state = {}
        for k, v in state.items():
            safe_state[k] = v if isinstance(v, (dict, list, str, int, float, type(None), bool)) else _safe(v)

        with open(hist_path, 'w', encoding='utf-8') as f:
            json.dump(safe_state, f, ensure_ascii=False, indent=2)

        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(safe_state, f, ensure_ascii=False, indent=2)

        print(f"[Orchestrator] Memory saved: {hist_path}")


# Factory function
def create_orchestrator(llm_provider: str = None, model_name: str = None) -> OrchestratorAgent:
    """Create an OrchestratorAgent with specified LLM configuration.

    If no provider/model are supplied, fall back to values from `backend.config.Config`.
    """
    provider = llm_provider or Config.LLM_PROVIDER
    model = model_name or Config.MODEL_NAME

    return OrchestratorAgent(llm_provider=provider, model_name=model)

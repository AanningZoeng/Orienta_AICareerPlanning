# Multi-Agent Architecture Documentation

## Overview

The AI Career Path Planner uses a sophisticated multi-agent system built on **SpoonOS framework** to provide intelligent career guidance through parallel reasoning and coordinated execution.

## Architecture Principles

### Interoperable AI Systems

This system demonstrates three key principles of interoperable AI:

1. **Talk**: Agents communicate through structured state management
2. **Reason**: Each agent has specialized reasoning capabilities
3. **Collaborate**: Orchestrator coordinates parallel execution

### Agent Coordination Pattern

The system uses SpoonOS **StateGraph** for declarative workflow orchestration:

```python
StateGraph Workflow:
User Query → MajorResearchAgent → CareerAnalysisAgent → FuturePathAgent → Results
                    ↓                      ↓                    ↓
            WebScraperTool          MediaFinderTool    LinkedInAnalyzerTool
```

## Agent Descriptions

### 1. MajorResearchAgent

**Purpose**: University major research and recommendation

**Capabilities**:
- Analyzes user interests using LLM reasoning
- Recommends 3-5 relevant majors
- Uses WebScraperTool to gather university information
- Structures major data with descriptions, requirements, and resources

**Tools**:
- `WebScraperTool`: Simulates scraping university websites

**Key Methods**:
- `analyze_user_interests(query)`: LLM-powered interest analysis
- `research_majors(major_names)`: Detailed major information gathering

**Output**: List of major objects with full details

---

### 2. CareerAnalysisAgent

**Purpose**: Career path identification and analysis

**Capabilities**:
- Maps majors to potential careers
- Researches salary ranges and benefits
- Finds professional resources (YouTube, blogs, interviews)
- Analyzes job market outlook

**Tools**:
- `MediaFinderTool`: Discovers educational content and professional interviews

**Key Methods**:
- `identify_careers(major_name)`: Maps major to career paths
- `analyze_career(career_title)`: Detailed career analysis

**Output**: List of career objects with salary, benefits, and resources

---

### 3. FuturePathAgent

**Purpose**: Career progression forecasting

**Capabilities**:
- Analyzes career progression patterns
- Calculates promotion/transition statistics
- Uses LinkedIn-style data for insights
- Generates actionable recommendations

**Tools**:
- `LinkedInAnalyzerTool`: Analyzes career progression statistics

**Key Methods**:
- `analyze_progression(career_title, years)`: Statistical analysis
- `_generate_insights(stats)`: Creates actionable insights

**Output**: Future path objects with statistics and progressions

---

### 4. OrchestratorAgent (Master Coordinator)

**Purpose**: Multi-agent workflow orchestration

**Capabilities**:
- Manages StateGraph execution flow
- Coordinates parallel agent execution
- Handles error recovery
- Compiles final results

**Graph Nodes**:
1. `research_majors_node`: Executes MajorResearchAgent
2. `analyze_careers_node`: Executes CareerAnalysisAgent for all majors
3. `project_future_paths_node`: Executes FuturePathAgent for all careers
4. `compile_results_node`: Structures final output

**State Management**:
```python
CareerPlanningState:
    - user_query: str
    - majors: List[Dict]
    - careers: Dict[str, List[Dict]]
    - future_paths: Dict[str, List[Dict]]
    - result: Dict
    - error: Optional[str]
```

 **Workflow Execution**:
- Uses **DeclarativeGraphBuilder** for clean graph definition
- Implements sequential execution with error handling
- Could be extended for parallel execution groups

---

## Communication Flow

### 1. User Query Processing

```
User Input → Orchestrator.process_query()
    ↓
Initialize CareerPlanningState
    ↓
Compile StateGraph
    ↓
Execute graph.invoke(initial_state)
```

### 2. Agent Execution

Each agent node:
1. Receives current state
2. Executes specialized logic
3. Updates state with results
4. Passes to next node

### 3. State Updates

```python
State flows through nodes:
    
{user_query} 
    → {user_query, majors} 
    → {user_query, majors, careers}
    → {user_query, majors, careers, future_paths}
    → {result}
```

## Technical Depth Highlights

### 1. Intelligent Routing

While this implementation uses sequential execution, SpoonOS supports:
- **Conditional edges**: Route based on state
- **Parallel groups**: Execute multiple nodes simultaneously
- **LLM-powered routing**: Dynamic path selection

### 2. Memory Integration

Agents can leverage SpoonOS memory systems for:
- Short-term memory: Conversation context
- Long-term memory: Historical patterns
- Graph memory: Workflow state persistence

### 3. Error Handling

The orchestrator implements:
- Try-catch blocks in each node
- Error state tracking
- Graceful degradation
- Detailed logging

### 4. Scalability

The architecture can scale to:
- More specialized agents (e.g., EducationCostAgent, SkillGapAgent)
- Parallel execution for faster processing
- External API integrations
- Real-time data sources

## Custom Tools

### WebScraperTool

```python
class WebScraperTool(BaseTool):
    name = "web_scraper"
    - Simulates university website scraping
    - Returns structured major data
    - Mock implementation for demo
```

### LinkedInAnalyzerTool

```python
class LinkedInAnalyzerTool(BaseTool):
    name = "linkedin_analyzer"
    - Simulates LinkedIn career data analysis
    - Calculates progression statistics
    - Returns detailed insights
```

### MediaFinderTool

```python
class MediaFinderTool(BaseTool):
    name = "media_finder"
    - Finds YouTube videos/channels
    - Discovers blogs and articles
    - Locates professional interviews
```

## Real-World Extensions

### Production Enhancements

1. **Real Data Sources**:
   - Actual university API integrations
   - LinkedIn API for real career data
   - YouTube Data API for videos

2. **Advanced Reasoning**:
   - LLM-powered career matching
   - Personalized recommendation algorithms
   - Sentiment analysis on resources

3. **Parallel Execution**:
   - Process multiple majors simultaneously
   - Parallel career analysis
   - Concurrent data fetching

4. **Caching & Performance**:
   - Redis for result caching
   - Database for historical data
   - CDN for static content

## Conclusion

This multi-agent system demonstrates SpoonOS's power in building **interoperable, collaborative AI systems**. The architecture is:

✅ **Modular**: Each agent has clear responsibilities  
✅ **Extensible**: Easy to add new agents or tools  
✅ **Maintainable**: Clean separation of concerns  
✅ **Scalable**: Can handle increased complexity  
✅ **Production-Ready**: With minimal modifications

The system showcases how modern AI frameworks enable sophisticated, real-world applications through agent collaboration and intelligent orchestration.

import operator
import json
from typing import Annotated, List, Dict, Union, Any
from typing_extensions import TypedDict
import os
from dotenv import load_dotenv
load_dotenv()
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from agent_prompt_library import analyst_system_prompt, architect_system_prompt
from retrieve import Graph_Retrieval
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from agent_prompt_library import read_prompt

# --- CONFIGURATION ---
LLM_MODEL = "gemma3:27b" 
MAX_ITERATIONS = 3   

# --- 1. STATE DEFINITION ---
class AgentState(TypedDict):
    brd_summary: str
    high_level_tasks: List[str]
    roles: List[str]
    
    # Internal state
    iterations: int
    gathered_knowledge: Annotated[List[str], operator.add] 
    pending_questions: List[str]
    
    # Final Output
    final_user_stories: Dict[str, List[str]]

# --- 2. LLM SETUP ---
llm = ChatOllama(
    model=LLM_MODEL, 
    temperature=0, 
    format="json", 
    base_url=os.environ['OLLAMA_API_ADDRESS'], 
    num_ctx=100000
)

# --- 3. RETRIEVAL & TOOLS SETUP ---
ret = Graph_Retrieval(db_name='scalex_test1', collection_name='scalex_collect11')
tool_llm = ChatOllama(
    model="gemma3:27b", 
    temperature=0, 
    base_url=os.environ['OLLAMA_API_ADDRESS'], 
    num_ctx=100000, 
    format='json'
)

reader_prompt = PromptTemplate.from_template(read_prompt)

# --- 4. NODE DEFINITIONS ---

def analyst_node(state: AgentState):
    """
    [Decision Node] Acts as the Strategic Planner.
    
    Function:
    1. Reviews the Project Scope (BRD + High-Level Tasks) against the Target Roles.
    2. Scans 'gathered_knowledge' to see what technical details are already known.
    3. Determines if the current information is sufficient ('READY') or if information gaps exist ('RESEARCH').
    
    Outputs:
    - 'pending_questions': A list of specific queries for the Knowledge Base if status is RESEARCH.
    - 'status': implicitly drives the next step via the conditional edge.
    """
    iteration = state.get("iterations", 0)
    
    # Safety Valve: Prevent infinite research loops by forcing a proceed state
    if iteration >= MAX_ITERATIONS:
        return {"pending_questions": [], "iterations": iteration + 1}

    prompt = ChatPromptTemplate.from_messages([
        ("system", analyst_system_prompt),
        ("human", """
        BRD: {brd}
        TASKS: {tasks}
        ROLES: {roles}
        CURRENT KNOWLEDGE: {knowledge}
        """)
    ])
    
    chain = prompt | llm
    
    response = chain.invoke({
        "brd": state["brd_summary"],
        "tasks": state["high_level_tasks"],
        "roles": state["roles"],
        "knowledge": state.get("gathered_knowledge", [])
    })
    
    try:
        content = json.loads(response.content)
        status = content.get("status", "READY")
        payload = content.get("content", [])
    except:
        # Fallback: If JSON parsing fails, assume we have enough or risk breaking the flow.
        # Alternatively, could return 'pending_questions': [] to force movement to Architect.
        status = "READY"
        payload = []

    if status == "RESEARCH" and isinstance(payload, list) and len(payload) > 0:
        return {"pending_questions": payload, "iterations": iteration + 1}
    else:
        # Clear questions to signal the conditional edge to route to Architect
        return {"pending_questions": [], "iterations": iteration + 1}

def knowledge_base_node(state: AgentState):
    """
    [Execution Node] Acts as the Technical Researcher.
    
    Function:
    1. Receives specific queries ('pending_questions') from the Analyst.
    2. Performs Graph Retrieval (Gravity Retrieval) to fetch relationship-heavy context.
    3. Uses a 'Reader LLM' pattern to summarize the raw graph data into concise answers.
    
    Design Note:
    - We bypass standard Tool calling here for direct control over the retrieval + summarization pipeline.
    - This ensures raw graph data is cleaned before polluting the main Agent's context window.
    """
    questions = state.get("pending_questions", [])
    new_knowledge = []
    
    print(f"\n--- [KB Agent] Researching {len(questions)} questions ---")
    
    for q in questions:
        # 1. Fetch Raw Data (Graph Retrieval Only)
        raw_text = ret.gravity_retrieval(query=q)
        
        # 2. Synthesize Answer using the Reader/Summarizer Chain
        chain = reader_prompt | tool_llm
        answer_payload = chain.invoke({"context": raw_text, "question": q})
        
        # Handle potential object or string return types from the chain
        answer_text = answer_payload.content if hasattr(answer_payload, 'content') else str(answer_payload)
        
        new_knowledge.append(f"Q: {q}\nA: {answer_text}")
        
    return {"gathered_knowledge": new_knowledge}

def architect_node(state: AgentState):
    """
    [Synthesis Node] Acts as the Technical Product Owner.
    
    Function:
    1. Aggregates all context: The original Goal (BRD/Tasks) + The Researched Facts (Knowledge).
    2. Generates detailed User Stories mapped strictly to the 'roles' schema.
    3. Ensures stories are technical, actionable, and cover the acceptance criteria discovered during research.
    """
    print("\n--- [Architect] Generating Stories ---")
    prompt = ChatPromptTemplate.from_messages([
        ("system", architect_system_prompt),
        ("human", """
        BRD: {brd}
        TASKS: {tasks}
        ROLES: {roles}
        KNOWLEDGE: {knowledge}
        """)
    ])
    
    chain = prompt | llm
    
    response = chain.invoke({
        "brd": state["brd_summary"],
        "tasks": state["high_level_tasks"],
        "roles": state["roles"],
        "knowledge": state.get("gathered_knowledge", [])
    })
    
    try:
        final_stories = json.loads(response.content)
    except:
        final_stories = {"error": "Failed to parse JSON", "raw": response.content}
        
    return {"final_user_stories": final_stories}

# --- 5. EDGE LOGIC & GRAPH ---
# (Remaining graph construction code is fine as-is...)
# --- 5. EDGE LOGIC ---

def should_continue(state: AgentState):
    """
    Decides the path based on whether there are pending questions.
    """
    if state["pending_questions"] and len(state["pending_questions"]) > 0:
        return "research"
    return "generate"

# --- 6. GRAPH CONSTRUCTION ---

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("analyst", analyst_node)
workflow.add_node("knowledge_base", knowledge_base_node)
workflow.add_node("architect", architect_node)

# Set Entry Point
workflow.set_entry_point("analyst")

# Add Edges
workflow.add_conditional_edges(
    "analyst",
    should_continue,
    {
        "research": "knowledge_base",
        "generate": "architect"
    }
)

# Connect KB back to Analyst to re-evaluate
workflow.add_edge("knowledge_base", "analyst")

# End after architect
workflow.add_edge("architect", END)

# Compile
app = workflow.compile()

# --- 7. EXECUTION ---

def run_planner_agent(input_params, roles = []):
    brd_summary = input_params['brd']
    high_level_tasks = input_params['tasks']
    # Input Data
    # brd_summary = "An e-commerce module for selling digital art. Users need to purchase via credits."
    # high_level_tasks = [
    #     "Implement 'Add to Cart' functionality",
    #     "Create Credit Deduction API"
    # ]
    # roles = ["backend_dev", "frontend_dev", "qa"]

    inputs = {
        "brd_summary": brd_summary,
        "high_level_tasks": high_level_tasks,
        "roles": roles,
        "iterations": 1,
        "gathered_knowledge": [],
        "pending_questions": []
    }

    print("Starting Agent Workflow...")
    
    # Run the graph
    final_state = app.invoke(inputs)
    
    print("\n\n=== FINALIZING OUTPUT ===")
    # print(json.dumps(final_state["final_user_stories"], indent=2))
    return json.dumps(final_state["final_user_stories"])
# if __name__ == "__main__":
#     run_planner_agent()
import json
import operator
import os
from typing import Annotated, List, Dict, Any
from typing_extensions import TypedDict
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# --- IMPORTS ---
# Ensure ba_agent.py and planner_agent.py are in the same directory
from ba_agent import run_ba_agent
from planner_agent import run_planner_agent

load_dotenv()

# --- CONFIGURATION ---
LLM_MODEL = "gemma3:27b" # Orchestrator's brain
BASE_URL = os.environ.get('OLLAMA_API_ADDRESS')

# Enhanced Roster with "Skills" for the LLM to use
# This global variable is monkey-patched by the API for per-request customization
TEAM_ROSTER = [
    {"name": "Alice", "role": "backend_dev", "skills": "Python, API Design, SQL, High Scale"},
    {"name": "Bob", "role": "frontend_dev", "skills": "React, CSS, Accessibility, Dashboards"},
    {"name": "Charlie", "role": "qa", "skills": "Automation, Security Testing, Edge Cases"}
]

# --- 1. STATE DEFINITION ---

def merge_dicts(a: Dict, b: Dict) -> Dict:
    """Helper to merge dictionary outputs from the planner loop."""
    return {**a, **b}

class ProjectState(TypedDict):
    # Inputs
    project_brief: str
    
    # BA Outputs (The Structured Data)
    brd_summary: str
    modules: List[Dict[str, Any]] 
    
    # Planner Outputs (Accumulated across modules)
    # We use 'merge_dicts' so each step adds to the existing dict instead of overwriting
    module_stories: Annotated[Dict[str, Dict[str, List[str]]], merge_dicts]
    
    # Loop Control
    current_module_index: int
    
    # Human Input
    prioritized_stories: List[Dict[str, Any]]
    
    # Final Output
    assigned_tasks: Dict[str, List[str]]

# --- 2. ORCHESTRATOR LLM SETUP ---
llm = ChatOllama(model=LLM_MODEL, temperature=0, format="json", base_url=BASE_URL, num_ctx=100000)

allocator_prompt = """
You are a Technical Lead. Assign the following User Stories to the team based on their skills.

Team Roster:
{roster}

Stories to Assign (referenced by ID):
{story_list}

Instructions:
1. Analyze the complexity and tech stack of each story.
2. Assign the **Story ID** to the most suitable team member.
3. If a story fits no one, assign its ID to "Unassigned".

Output STRICT JSON where values are LISTS OF INTEGERS (IDs):
{{
    "Alice": [0, 2, 5],
    "Bob": [1, 3],
    "Charlie": [4],
    "Unassigned": []
}}
"""

# --- 3. NODES ---

def ba_node(state: ProjectState):
    """
    Invokes the BA Agent to generate the project summary and module breakdown.
    Initializes the loop counters for the planner.
    """
    print("--- [Orchestrator] Invoking BA Agent ---")
    
    output = run_ba_agent(state["project_brief"]) 
    # print('modules - ', output.get('modules'))
    # print('module1 - ', output.get('modules')[0])
    return {
        "brd_summary": output.get("brd_summary", ""), 
        "modules": [output.get("modules", [])[0]], # Remove this zero for full processing.
        "current_module_index": 0, # Start at the first module
        "module_stories": {}       # Initialize empty story dict
    }

def planner_step_node(state: ProjectState):
    """
    Processes ONLY the current module pointed to by 'current_module_index'.
    This allows granular status updates and state saving per module.
    """
    idx = state["current_module_index"]
    modules = state["modules"]
    
    # Safety check: Stop if index is out of bounds
    if idx >= len(modules):
        return {}

    current_module = modules[idx]
    mod_name = current_module["module_name"]
    mod_tasks = current_module["tasks"]
    
    print(f"--- [Orchestrator] Planning Module {idx+1}/{len(modules)}: {mod_name} ---")
    
    roles = [member["role"] for member in TEAM_ROSTER]
    
    input_params = {
        "brd": state["brd_summary"],
        "tasks": mod_tasks
    }
    
    # Run Planner Agent for this specific slice
    story_json_str = run_planner_agent(input_params, roles)
    
    try:
        story_dict = json.loads(story_json_str)
    except json.JSONDecodeError:
        print(f"   ! Error parsing JSON from planner for {mod_name}")
        story_dict = {}

    # Return partial update
    # 1. Add new stories to 'module_stories' (via merge_dicts)
    # 2. Increment 'current_module_index' for the next loop
    res = {
        "module_stories": {mod_name: story_dict}, 
        "current_module_index": idx + 1           
    }
    print(res, '->Planner response')
    return {
        "module_stories": {mod_name: story_dict}, 
        "current_module_index": idx + 1           
    }

def prioritization_node(state: ProjectState):
    """
    Flattens the module-wise stories into a single list for human review.
    """
    print("--- [Orchestrator] Preparing for Human Prioritization ---")
    
    flat_stories = []
    
    for mod_name, role_dict in state["module_stories"].items():
        if not isinstance(role_dict, dict): continue # Safety check
        
        for role, stories in role_dict.items():
            for story in stories:
                # Structure for the Human Review
                flat_stories.append({
                    "module": mod_name,
                    "role": role, 
                    "story": story, 
                    "priority": "medium" # Default priority
                })
            
    return {"prioritized_stories": flat_stories}

def allocator_node(state: ProjectState):
    """
    Uses the LLM to assign IDs, then maps them back to full objects.
    """
    print("--- [Orchestrator] AI Allocating Tasks (ID-Based) ---")
    
    prioritized = state["prioritized_stories"]
    
    # 1. Create a simplified list for the LLM to read (saves tokens, reduces confusion)
    llm_view_list = []
    for i, item in enumerate(prioritized):
        story_content = item["story"]
        if isinstance(story_content, dict):
            # Extract relevant fields for decision making
            description = f"[{item['role']}] {story_content.get('ticket_title', 'Unknown')} - {story_content.get('user_story', '')}"
        else:
            description = f"[{item['role']}] {str(story_content)}"
            
        llm_view_list.append(f"ID {i}: {description}")
    
    # 2. Invoke LLM
    roster_text = json.dumps(TEAM_ROSTER, indent=2)
    stories_text = "\n".join(llm_view_list)
    
    prompt = ChatPromptTemplate.from_template(allocator_prompt)
    chain = prompt | llm
    
    try:
        response = chain.invoke({"roster": roster_text, "story_list": stories_text})
        id_assignments = json.loads(response.content)
    except Exception as e:
        print(f"Allocator LLM Error: {e}")
        # Fallback: Assign everything to Unassigned
        id_assignments = {"Unassigned": list(range(len(prioritized)))}
            
    # 3. Reconstruct the Full Rich Objects
    final_assignments = {member["name"]: [] for member in TEAM_ROSTER}
    final_assignments["Unassigned"] = []
    
    for person, ids in id_assignments.items():
        if person not in final_assignments:
            final_assignments[person] = []
            
        for story_id in ids:
            try:
                # Retrieve the full rich object from the original list using the ID
                full_story_obj = prioritized[int(story_id)]["story"]
                # Optionally inject priority if needed
                if isinstance(full_story_obj, dict):
                    full_story_obj['priority'] = prioritized[int(story_id)].get('priority', 'medium')
                    
                final_assignments[person].append(full_story_obj)
            except (IndexError, ValueError):
                continue 

    return {"assigned_tasks": final_assignments}

# --- 4. EDGE LOGIC (THE LOOP) ---

def check_next_step(state: ProjectState):
    """
    Decides if we loop back to planner or move to prioritization.
    """
    if state["current_module_index"] < len(state["modules"]):
        return "continue_planning"
    return "finish_planning"

# --- 5. GRAPH CONSTRUCTION ---

workflow = StateGraph(ProjectState)

workflow.add_node("ba_agent", ba_node)
workflow.add_node("planner_step", planner_step_node) # Sequential Loop Node
workflow.add_node("human_review", prioritization_node)
workflow.add_node("allocator", allocator_node)

workflow.set_entry_point("ba_agent")

# Logic: BA -> Planner
workflow.add_edge("ba_agent", "planner_step")

# Logic: Planner Loop
workflow.add_conditional_edges(
    "planner_step",
    check_next_step,
    {
        "continue_planning": "planner_step", # LOOP BACK
        "finish_planning": "human_review"    # EXIT LOOP
    }
)

# Logic: Review -> Allocator -> End
workflow.add_edge("human_review", "allocator")
workflow.add_edge("allocator", END)

# Persistence
memory = MemorySaver()

# Compile with interrupt for Human-in-the-Loop
app = workflow.compile(
    checkpointer=memory, 
    interrupt_after=["human_review"] 
)

# --- 6. EXECUTION SIMULATION ---

def run_orchestrator():
    thread_id = {"configurable": {"thread_id": "project_beta_01"}}
    
    initial_input = {
        "project_brief": "Build PalTech Prospect Portal."
    }

    print(">>> STARTING PHASE 1: GENERATION")
    
    # 1. Run until Human Interrupt
    # Because we loop, we will see "Planning Module X/Y" prints multiple times
    for event in app.stream(initial_input, thread_id):
        pass 
    
    # 2. Human Review Interruption
    current_state = app.get_state(thread_id).values
    print("\n\n>>> PAUSED FOR HUMAN REVIEW (Mock UI)")
    
    stories = current_state["prioritized_stories"]
    print(f"System generated {len(stories)} stories across {current_state['current_module_index']} modules.")
    
    # 3. Resume with Allocation
    print("\n>>> RESUMING: ALLOCATION")
    final_output = None
    
    for event in app.stream(None, thread_id):
        if "allocator" in event:
            final_output = event["allocator"]

    print("\n=== FINAL TEAM ASSIGNMENTS (AI GENERATED) ===")
    
    # Optional: Save to file
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(final_output['assigned_tasks'], f, indent=2)
        
    print(json.dumps(final_output["assigned_tasks"], indent=2))

if __name__ == "__main__":
    run_orchestrator()
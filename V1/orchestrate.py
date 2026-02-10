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
# Ensure these files are in the same directory
from ba_agent import run_ba_agent
from planner_agent import run_planner_agent

load_dotenv()

# --- CONFIGURATION ---
LLM_MODEL = "gemma3:27b" # Orchestrator's brain
BASE_URL = os.environ.get('OLLAMA_API_ADDRESS')

# Enhanced Roster with "Skills" for the LLM to use
TEAM_ROSTER = [
    {"name": "Alice", "role": "backend_dev", "skills": "Python, API Design, SQL, High Scale"},
    {"name": "Bob", "role": "frontend_dev", "skills": "React, CSS, Accessibility, Dashboards"},
    {"name": "Charlie", "role": "qa", "skills": "Automation, Security Testing, Edge Cases"}
]

# --- 1. STATE DEFINITION ---
class ProjectState(TypedDict):
    # Inputs
    project_brief: str
    
    # BA Outputs (The Structured Data)
    brd_summary: str
    modules: List[Dict[str, Any]] 
    
    # Planner Outputs (Accumulated across modules)
    # Structure: { "Module Name": { "backend_dev": [stories], ... } }
    module_stories: Dict[str, Dict[str, List[str]]]
    
    # Human Input
    prioritized_stories: List[Dict[str, Any]]
    
    # Final Output
    assigned_tasks: Dict[str, List[str]]

# --- 2. ORCHESTRATOR LLM SETUP ---
llm = ChatOllama(model=LLM_MODEL, temperature=0, format="json", base_url=BASE_URL, num_ctx=100000)

# allocator_prompt = """
# You are a Technical Lead and Resource Manager.
# Your goal is to assign User Stories to the most appropriate team member based on their Role and Skills.

# Team Roster:
# {roster}

# Pending User Stories:
# {stories}

# Instructions:
# 1. Review each story's technical requirements.
# 2. Assign it to the team member whose role matches and whose skills are the best fit.
# 3. If a story requires a role not present (e.g., DevOps), assign it to "Unassigned".

# Output strict JSON:
# {{
#     "Alice": ["Story 1...", "Story 2..."],
#     "Bob": ["Story 3..."],
#     "Charlie": ["Story 4..."],
#     "Unassigned": []
# }}
# """

# --- 3. NODES ---

def ba_node(state: ProjectState):
    """
    Invokes the BA Agent.
    """
    print("--- [Orchestrator] Invoking BA Agent ---")
    
    # run_ba_agent returns a dict: {'brd_summary': ..., 'modules': [...]}
    output = run_ba_agent(state["project_brief"]) 
    
    return {
        "brd_summary": output.get("brd_summary", ""), 
        "modules": output.get("modules", [])
    }

def planner_node(state: ProjectState):
    """
    Iterates through every Module found by the BA and runs the Planner Agent on it.
    """
    print("--- [Orchestrator] Invoking Planner Agent (Per Module) ---")
    
    roles = [member["role"] for member in TEAM_ROSTER]
    all_module_stories = {}
    
    # The Loop: Process one module at a time
    for module in state["modules"]:
        mod_name = module["module_name"]
        mod_tasks = module["tasks"]
        print(f"   > Planning for Module: {mod_name}")
        
        # Prepare inputs for Planner Agent
        input_params = {
            "brd": state["brd_summary"],
            "tasks": mod_tasks
        }
        
        # Call Planner
        # NOTE: run_planner_agent returns a JSON STRING based on your code
        story_json_str = run_planner_agent(input_params, roles)
        
        try:
            story_dict = json.loads(story_json_str)
        except json.JSONDecodeError:
            print(f"   ! Error parsing JSON from planner for {mod_name}")
            story_dict = {}

        all_module_stories[mod_name] = story_dict
        break
        
    return {"module_stories": all_module_stories}

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
# ... (imports remain the same) ...

# --- NEW ALLOCATOR PROMPT (ID BASED) ---
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

# ... (ba_node, planner_node, prioritization_node remain the same) ...

def allocator_node(state: ProjectState):
    """
    Uses the LLM to assign IDs, then maps them back to full objects.
    """
    print("--- [Orchestrator] AI Allocating Tasks (ID-Based) ---")
    
    prioritized = state["prioritized_stories"]
    
    # 1. Create a simplified list for the LLM to read (saves tokens, reduces confusion)
    # We only send the index, role, and title/story to the LLM.
    llm_view_list = []
    for i, item in enumerate(prioritized):
        # Handle cases where 'story' is a dict (Rich Ticket) or string (Simple)
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
        # Expected: {"Alice": [0, 1], "Bob": [2]}
        id_assignments = json.loads(response.content)
    except Exception as e:
        print(f"Allocator LLM Error: {e}")
        # Fallback: Assign everything to Unassigned if it crashes
        id_assignments = {"Unassigned": list(range(len(prioritized)))}
            
    # 3. Reconstruct the Full Rich Objects
    # We map the IDs back to the original 'prioritized' objects
    final_assignments = {member["name"]: [] for member in TEAM_ROSTER}
    final_assignments["Unassigned"] = []
    
    for person, ids in id_assignments.items():
        if person not in final_assignments:
            final_assignments[person] = []
            
        for story_id in ids:
            try:
                # Retrieve the full rich object from the original list
                full_story_obj = prioritized[int(story_id)]["story"]
                final_assignments[person].append(full_story_obj)
            except IndexError:
                continue # Skip invalid IDs

    return {"assigned_tasks": final_assignments}


def allocator_node_v1(state: ProjectState):
    """
    Uses the Orchestrator LLM to intelligently assign tasks.
    """
    print("--- [Orchestrator] AI Allocating Tasks to Team ---")
    
    prioritized = state["prioritized_stories"]
    
    # Convert list to string for Prompt
    stories_text = json.dumps(prioritized, indent=2)
    roster_text = json.dumps(TEAM_ROSTER, indent=2)
    
    prompt = ChatPromptTemplate.from_template(allocator_prompt)
    chain = prompt | llm
    
    try:
        response = chain.invoke({"roster": roster_text, "stories": stories_text})
        assignments = json.loads(response.content)
    except Exception as e:
        print(f"Allocator LLM Error: {e}")
        assignments = {"Error": ["Manual assignment required due to LLM failure"]}
            
    return {"assigned_tasks": assignments}

# --- 4. GRAPH CONSTRUCTION ---

workflow = StateGraph(ProjectState)

workflow.add_node("ba_agent", ba_node)
workflow.add_node("planner_agent", planner_node)
workflow.add_node("human_review", prioritization_node)
workflow.add_node("allocator", allocator_node)

# Flow
workflow.set_entry_point("ba_agent")
workflow.add_edge("ba_agent", "planner_agent")
workflow.add_edge("planner_agent", "human_review")
workflow.add_edge("human_review", "allocator")
workflow.add_edge("allocator", END)

# Persistence
memory = MemorySaver()

# Compile with interrupt for Human-in-the-Loop
app = workflow.compile(
    checkpointer=memory, 
    interrupt_after=["human_review"] 
)

# --- 5. EXECUTION ---

def run_orchestrator():
    thread_id = {"configurable": {"thread_id": "project_beta_01"}}
    
    initial_input = {
        "project_brief": "Build  PalTech Prospect Portal, a secure and exclusive platform aimed at building trust with potential high-value clients."
    }

    print(">>> STARTING PHASE 1: GENERATION")
    
    # 1. Run until Human Interrupt
    for event in app.stream(initial_input, thread_id):
        pass 
    
    # 2. Human Review Interruption
    current_state = app.get_state(thread_id).values
    print("\n\n>>> PAUSED FOR HUMAN REVIEW (Mock UI)")
    
    stories = current_state["prioritized_stories"]
    print(f"System generated {len(stories)} stories across all modules.")
    
    # (Here is where you would present 'stories' to a frontend UI)
    # ... User reorders stories ...
    
    # 3. Resume with Allocation
    print("\n>>> RESUMING: ALLOCATION")
    final_output = None
    
    # We pass None to resume from the interrupted state
    for event in app.stream(None, thread_id):
        if "allocator" in event:
            final_output = event["allocator"]

    print("\n=== FINAL TEAM ASSIGNMENTS (AI GENERATED) ===")
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(final_output['assigned_tasks'], f, indent=2)
    print(json.dumps(final_output["assigned_tasks"], indent=2))

# if __name__ == "__main__":
#     run_orchestrator()
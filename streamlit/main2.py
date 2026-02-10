import streamlit as st
import json
import pandas as pd
import uuid
import time

# --- IMPORT YOUR ORCHESTRATOR ---
import orchestrate
from orchestrate import app as graph_app 

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Agentic PM Orchestrator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .ticket-card {
        background-color: #f0f2f6;
        border-left: 5px solid #ff4b4b;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .ticket-title {
        font-weight: bold;
        font-size: 1.1em;
        color: #31333F;
    }
    .ticket-meta {
        font-size: 0.8em;
        color: #666;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "current_stage" not in st.session_state:
    st.session_state.current_stage = "INPUT" 

if "graph_thread" not in st.session_state:
    st.session_state.graph_thread = {"configurable": {"thread_id": st.session_state.session_id}}

if "ba_summary" not in st.session_state:
    st.session_state.ba_summary = None

if "story_df" not in st.session_state:
    st.session_state.story_df = None

# NEW: Store the raw objects separately from the DataFrame
if "all_story_objects" not in st.session_state:
    st.session_state.all_story_objects = []

# --- SIDEBAR ---
with st.sidebar:
    st.title("🤖 Agentic PM")
    st.markdown("---")
    
    st.header("1. Project Scope")
    default_brief = "Build PalTech Prospect Portal, a secure and exclusive platform aimed at building trust with potential high-value clients."
    project_brief = st.text_area("Project Brief", value=default_brief, height=150)
    
    uploaded_file = st.file_uploader("Upload BRD (PDF)", type="pdf")
    if uploaded_file:
        st.success(f"✅ Loaded: {uploaded_file.name}")
        st.info("⚠️ PDF ingestion is currently bypassed.")

    st.markdown("---")
    st.header("2. Team Roster")
    
    if "roster_data" not in st.session_state:
        st.session_state.roster_data = pd.DataFrame(orchestrate.TEAM_ROSTER)

    edited_roster = st.data_editor(
        st.session_state.roster_data,
        num_rows="dynamic",
        column_config={
            "name": "Name",
            "role": "Role",
            "skills": "Skills Context"
        },
        use_container_width=True,
        key="roster_editor"
    )

    st.markdown("---")
    if st.button("🔄 Reset System"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- MAIN LOGIC ---

# ---------------------------------------------------------
# STAGE 1: INPUT & GENERATION
# ---------------------------------------------------------
if st.session_state.current_stage == "INPUT":
    st.subheader("🚀 Start New Project Analysis")
    st.write("Click below to trigger the BA and Planner agents.")
    
    if st.button("Start Analysis Workflow", type="primary"):
        if not project_brief:
            st.error("Please provide a project brief.")
            st.stop()
            
        orchestrate.TEAM_ROSTER = edited_roster.to_dict(orient="records")
        
        status_container = st.status("Agents are working...", expanded=True)
        
        try:
            status_container.write("🕵️‍♂️ **BA Agent:** Analyzing business requirements...")
            
            inputs = {"project_brief": project_brief}
            
            # Consume the stream
            for event in graph_app.stream(inputs, st.session_state.graph_thread):
                for key, value in event.items():
                    status_container.write(f"✅ **{key}** completed successfully.")
            
            status_container.update(label="Planning Complete! Waiting for Review.", state="complete", expanded=False)
            
            # Fetch State
            snapshot = graph_app.get_state(st.session_state.graph_thread)
            current_state_values = snapshot.values
            
            st.session_state.ba_summary = current_state_values.get("brd_summary", "No summary generated.")
            
            # FIX: Store raw objects in Session State, NOT in the DataFrame
            raw_stories = current_state_values.get("prioritized_stories", [])
            st.session_state.all_story_objects = raw_stories # Persist full objects
            
            # Create View DataFrame (Lightweight)
            flat_data = []
            for idx, item in enumerate(raw_stories):
                story_content = item["story"]
                title = "Unknown"
                desc = ""
                
                if isinstance(story_content, dict):
                    title = story_content.get("ticket_title", "Untitled")
                    desc = story_content.get("user_story", "")
                else:
                    title = str(story_content)[:50] + "..."
                    desc = str(story_content)
                
                flat_data.append({
                    "id": idx,  # CRITICAL: We map back using this ID
                    "Module": item.get("module", "General"),
                    "Role": item.get("role", "Unknown"),
                    "Ticket Title": title,
                    "User Story": desc,
                    "Priority": item.get("priority", "medium")
                })
            
            st.session_state.story_df = pd.DataFrame(flat_data)
            
            st.session_state.current_stage = "REVIEW"
            st.rerun()
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.stop()


# ---------------------------------------------------------
# STAGE 2: HUMAN REVIEW (HITL)
# ---------------------------------------------------------
elif st.session_state.current_stage == "REVIEW":
    st.success("✅ BA and Planning Phases Complete.")
    
    with st.expander("📄 View Business Requirements Summary", expanded=False):
        st.markdown(st.session_state.ba_summary)
    
    st.subheader("⚖️ Review & Prioritize User Stories")
    
    # Editable Table
    edited_df = st.data_editor(
        st.session_state.story_df,
        column_config={
            "id": None, # Hide the ID column
            "Module": st.column_config.TextColumn("Module", disabled=True),
            "Role": st.column_config.TextColumn("Role", disabled=True),
            "Priority": st.column_config.SelectboxColumn(
                "Priority", options=["critical", "high", "medium", "low"]
            )
        },
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🚀 Approve & Allocate", type="primary"):
            updated_stories_list = []
            
            # FIX: Iterate through DataFrame and lookup original object by ID
            for index, row in edited_df.iterrows():
                try:
                    obj_id = int(row["id"])
                    
                    # Retrieve the FULL original object from session state
                    original_item = st.session_state.all_story_objects[obj_id]
                    
                    # Apply the UI edit (Priority)
                    original_item["priority"] = row["Priority"]
                    
                    updated_stories_list.append(original_item)
                except (ValueError, IndexError, KeyError) as e:
                    # Handle cases where row might be new or id is missing
                    continue 

            # Update Graph State
            graph_app.update_state(
                st.session_state.graph_thread, 
                {"prioritized_stories": updated_stories_list}
            )
            
            with st.spinner("🤖 AI Allocator is assigning tickets..."):
                final_output = None
                for event in graph_app.stream(None, st.session_state.graph_thread):
                    if "allocator" in event:
                        final_output = event["allocator"]
                
                st.session_state.final_assignments = final_output["assigned_tasks"]
                st.session_state.current_stage = "RESULT"
                st.rerun()


# ---------------------------------------------------------
# STAGE 3: RESULTS
# ---------------------------------------------------------
elif st.session_state.current_stage == "RESULT":
    st.balloons()
    st.subheader("🎯 Final Allocation Board")
    
    assignments = st.session_state.final_assignments
    cols = st.columns(len(assignments))
    
    for i, (person, tickets) in enumerate(assignments.items()):
        with cols[i]:
            st.markdown(f"### 👤 {person}")
            st.caption(f"{len(tickets)} Tickets Assigned")
            st.divider()
            
            for t in tickets:
                if isinstance(t, dict):
                    title = t.get('ticket_title', 'Untitled')
                    story = t.get('user_story', 'No details')
                    ac_list = t.get('acceptance_criteria', [])
                    notes = t.get('technical_notes', '')
                    
                    with st.container():
                        st.markdown(f"""
                        <div class="ticket-card">
                            <div class="ticket-title">{title}</div>
                            <div class="ticket-meta">{story[:100]}...</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        with st.expander("Details"):
                            st.markdown(f"**User Story:**\n{story}")
                            if ac_list:
                                st.markdown("**Acceptance Criteria:**")
                                for ac in ac_list:
                                    st.markdown(f"- {ac}")
                            if notes:
                                st.info(f"**Tech Notes:** {notes}")
                else:
                    st.warning(str(t))

    st.markdown("---")
    
    json_str = json.dumps(assignments, indent=2)
    st.download_button(
        label="📥 Download JSON",
        data=json_str,
        file_name="project_tickets.json",
        mime="application/json"
    )
    
    if st.button("Start New Project"):
        st.session_state.current_stage = "INPUT"
        st.rerun()
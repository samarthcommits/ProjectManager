import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Any, Optional
import uuid
import json
import asyncio
from fastapi.middleware.cors import CORSMiddleware


# Import your existing logic
import orchestrator_v1 
from orchestrator_v1 import app as graph_app 

app = FastAPI(title="Agentic PM API", version="1.1")

# --- CRITICAL FIX: ADD CORS MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (React, Lovable, etc.)
    allow_credentials=True,
    allow_methods=["*"],  # Allows POST, OPTIONS, GET, etc.
    allow_headers=["*"],  # Allows all headers
)
# -----------------------------------------
# --- Pydantic Models ---
class TeamMember(BaseModel):
    name: str
    role: str
    skills: str

class PlanRequest(BaseModel):
    project_brief: str
    roster: List[TeamMember]
    session_id: Optional[str] = None

class StoryReview(BaseModel):
    story: Any
    priority: str
    role: str
    module: str

class AllocateRequest(BaseModel):
    session_id: str
    approved_stories: List[StoryReview]

# --- Helper ---
def sse_format(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"

# --- Endpoints ---

@app.post("/plan")
async def generate_plan_stream(request: PlanRequest):
    thread_id = request.session_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Update Global Roster based on request
    orchestrator_v1.TEAM_ROSTER = [m.model_dump() for m in request.roster]

    async def event_generator():
        try:
            yield sse_format({"type": "status", "msg": "🚀 Starting BA Agent..."})
            
            initial_input = {"project_brief": request.project_brief}
            
            # Streaming the graph execution
            async for event in graph_app.astream(initial_input, config):
                for node_name, state_values in event.items():
                    
                    if node_name == "ba_agent":
                        count = len(state_values.get("modules", []))
                        yield sse_format({"type": "status", "msg": f"✅ Analysis Done. Identified {count} modules."})

                    elif node_name == "planner_step":
                        stories = state_values.get("module_stories", {})
                        if stories:
                            completed_module = list(stories.keys())[0]
                            yield sse_format({"type": "status", "msg": f"✅ Generated stories for: {completed_module}"})

                    # --- FIX START: Catch the node that runs AFTER planning loop ---
                    elif node_name == "human_review":
                        # This node runs exactly when the planner loop finishes.
                        # We send the specific keyword "Planning Complete" to satisfy the React UI.
                        yield sse_format({"type": "status", "msg": "✅ Planning Complete. Compiling Final Plan..."})
                    # --- FIX END ---
            
            # Fetch Final State
            snapshot = await graph_app.aget_state(config)
            
            yield sse_format({
                "type": "result", 
                "data": {
                    "session_id": thread_id,
                    "ba_summary": snapshot.values.get("brd_summary", ""),
                    "stories": snapshot.values.get("prioritized_stories", [])
                }
            })

        except Exception as e:
            print(f"Server Error: {e}")
            yield sse_format({"type": "error", "msg": str(e)})

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/allocate")
async def allocate_resources_stream(request: AllocateRequest):
    config = {"configurable": {"thread_id": request.session_id}}
    
    async def event_generator():
        try:
            yield sse_format({"type": "status", "msg": "📝 Saving priorities..."})
            
            # Update State (Sync is fine here, it's fast)
            stories_payload = [s.model_dump() for s in request.approved_stories]
            await graph_app.aupdate_state(config, {"prioritized_stories": stories_payload})
            
            yield sse_format({"type": "status", "msg": "🤖 AI Allocator is assigning tickets..."})
            
            final_output = None
            
            # --- CRITICAL FIX: Use async for + astream ---
            # Pass None to resume execution
            async for event in graph_app.astream(None, config):
                if "allocator" in event:
                    final_output = event["allocator"]
                    yield sse_format({"type": "status", "msg": "✅ Allocation Complete!"})
            
            if final_output:
                yield sse_format({"type": "result", "data": final_output})
            else:
                yield sse_format({"type": "error", "msg": "Allocator returned empty."})

        except Exception as e:
            yield sse_format({"type": "error", "msg": str(e)})

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8200)
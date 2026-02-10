import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Any, Optional
import uuid
import json
import asyncio

# Import your existing logic
import orchestrate 
from orchestrate import app as graph_app 

app = FastAPI(title="Agentic PM API", version="1.1")

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
    """
    Uses ASTREAM to ensure non-blocking updates.
    """
    thread_id = request.session_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Update Global Roster
    orchestrate.TEAM_ROSTER = [m.model_dump() for m in request.roster]

    async def event_generator():
        try:
            yield sse_format({"type": "status", "msg": "🚀 Starting BA Agent..."})
            
            initial_input = {"project_brief": request.project_brief}
            
            # --- CRITICAL FIX: Use async for + astream ---
            async for event in graph_app.astream(initial_input, config):
                for node_name, state_values in event.items():
                    
                    if node_name == "ba_agent":
                        # Send status update
                        yield sse_format({"type": "status", "msg": "✅ BA Analysis Complete. Starting Planner..."})
                        
                        # Optional: Send Module breakdown immediately?
                        modules = state_values.get("modules", [])
                        yield sse_format({"type": "status", "msg": f"📋 Planning stories for {len(modules)} modules..."})

                    elif node_name == "planner_agent":
                        yield sse_format({"type": "status", "msg": "✅ Planning Complete. Formatting..."})
            
            # Fetch Final State
            snapshot = await graph_app.aget_state(config) # Use async get
            
            if snapshot.values:
                result_payload = {
                    "session_id": thread_id,
                    "ba_summary": snapshot.values.get("brd_summary", ""),
                    "stories": snapshot.values.get("prioritized_stories", [])
                }
                yield sse_format({"type": "result", "data": result_payload})
            else:
                yield sse_format({"type": "error", "msg": "Graph failed to retain state."})

        except Exception as e:
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
    uvicorn.run(app, host="127.0.0.1", port=8100)
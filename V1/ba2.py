import operator
import inspect
import re
import os
from typing import Annotated, TypedDict, Union, List
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END, START
from dotenv import load_dotenv
from retrieve import Graph_Retrieval
import json
from agent_prompt_library import PM_PROMPT

load_dotenv()
ret = Graph_Retrieval(db_name='scalex_test1', collection_name='scalex_collect21')
# --- 1. SMART TOOLS (Reader-Retriever Pattern) ---
# These tools use a "Sub-LLM" to read the messy BRD and return clean answers.

tool_llm = ChatOllama(model="gemma3:27b", temperature=0, base_url=os.environ['OLLAMA_API_ADDRESS'], num_ctx=100000, format='json')

reader_prompt = PromptTemplate.from_template(
    """You are a Technical Business Analyst. 
    Read the provided context from the BRD (Business Requirements Document) and answer the question.
    
    - If the answer is in the context, summarize it clearly.
    - If the context is irrelevant, say "Information not found in this chunk."

    Context:
    {context}

    Question: 
    {question}

    Answer:"""
)

@tool
def retrieve_from_graph(query: str) -> str:
    """
    REQUIRED for questions about **relationships, workflows, and dependencies**.
    Use this when asking:
    - "Who are the stakeholders for Feature X?"
    - "What is the approval workflow?"
    - "What downstream systems are affected?"
    """
    # MOCK DATA: Simulating a Graph Retrieval Result
    
    # Inner LLM summarizes the raw text
    
    raw_text = ret.gravity_retrieval(query=query)
    chain = reader_prompt | tool_llm
    return chain.invoke({"context": raw_text, "question": query}).content

@tool
def retrieval_from_vectorstore(query: str) -> str:
    """
    REQUIRED for questions about **specific values, configurations, and static facts**.
    Use this when asking:
    - "Which database version is required?"
    - "What are the specific API endpoints?"
    - "What is the token expiry time?"
    - "What are the UI color codes?"
    """
    # MOCK DATA: Simulating a Vector Search Result
    raw_text = ret.dense_retrieval(query=query)
    
    chain = reader_prompt | tool_llm
    return chain.invoke({"context": raw_text, "question": query}).content

tools = [retrieve_from_graph, retrieval_from_vectorstore]
tool_map = {t.name: t for t in tools}

# --- 2. THE "PROJECT MANAGER" PROMPT ---
# This forces the specific "Summary -> Deep Dive -> Plan" behavior.



tool_desc_str = "\n".join([f"{t.name}: {t.description}" for t in tools])
tool_names_str = ", ".join([t.name for t in tools])

llm = ChatOllama(model="gemma3:27b", temperature=0, stop=["Observation:"], base_url=os.environ['OLLAMA_API_ADDRESS'], num_ctx=100000)

# --- 3. GRAPH DEFINITION ---

class AgentState(TypedDict):
    input: str
    history: Annotated[List[str], operator.add]
    final_answer: Union[str, None]

def ba_reason_node(state: AgentState):
    
    full_history = state.get("history", [])
    
    # Simple heuristic: If history is HUGE, keep the first item (Summary) and the last 6 items.
    # if len(full_history) > 8:
    #     scratchpad_items = full_history[:2] + full_history[-6:]
    # else:
    #     scratchpad_items = full_history
    scratchpad_items = full_history
    scratchpad = "".join(scratchpad_items)
    
    prompt_text = PM_PROMPT.format(
        tool_descriptions=tool_desc_str,
        tool_names=tool_names_str,
        input=state["input"],
        scratchpad=scratchpad
    )
    
    response = llm.invoke(prompt_text)
    return {"history": [response.content]}

def action_node(state: AgentState):
    last_message = state["history"][-1]
    
    action_match = re.search(r"Action:\s*([a-zA-Z0-9_]+)", last_message)
    input_match = re.search(r"Action Input:\s*(.+?)(?:\n|$)", last_message)
    
    if not action_match or not input_match:
        return {"history": ["\nObservation: Error parsing action. Please use correct format.\nThought:"]}

    tool_name = action_match.group(1).strip()
    tool_input_str = input_match.group(1).strip()

    if tool_name not in tool_map:
         return {"history": [f"\nObservation: Tool {tool_name} not found.\nThought:"]}

    try:
        selected_tool = tool_map[tool_name]
        # Direct string passing for these research tools
        result = selected_tool.invoke({"query": tool_input_str})
        output = f"\nObservation: {str(result)}\n"
    except Exception as e:
        output = f"\nObservation: Error: {e}\n"

    return {"history": [output]}

# ---- 4. COMPILE ----
workflow = StateGraph(AgentState)
workflow.add_node("reason", ba_reason_node)
workflow.add_node("act", action_node)
workflow.add_edge(START, "reason")
workflow.add_conditional_edges("reason", lambda x: END if "Final Answer:" in x["history"][-1] else "act")
workflow.add_edge("act", "reason")
app = workflow.compile()

# ---- 5. EXECUTION ----
# ... (Previous imports and graph definition remain the same) ...

# --- 6. PARSING HELPER ---
# We need this because the Orchestrator expects a Dictionary, but the Agent produces a String.
class BaOutputSchema(TypedDict):
    brd_summary: str
    tasks: List[str]

def parse_ba_response(final_text: str) -> dict:
    """
    Uses a small LLM call to convert the free-text 'Final Answer' 
    into the structured format required by the Orchestrator.
    """
    parser_llm = ChatOllama(
        model="gemma3:27b", 
        temperature=0, 
        format="json", 
        base_url=os.environ['OLLAMA_API_ADDRESS']
    )
    
    parsing_prompt = """
    You are a data parser. Extract the Project Summary and High-Level Tasks from the text below.
    
    Text: 
    {text}
    
    Output strictly in this JSON format:
    {{
        "brd_summary": "One or two sentence summary of the project",
        "tasks": ["Task 1", "Task 2", "Task 3"]
    }}
    """
    
    try:
        # Extract the actual content after "Final Answer:" if present
        clean_text = final_text.split("Final Answer:")[-1].strip()
        
        response = parser_llm.invoke(parsing_prompt.format(text=clean_text))
        return json.loads(response.content)
    except Exception as e:
        print(f"Error parsing BA output: {e}")
        # Fallback in case of parsing failure
        return {
            "brd_summary": "Error parsing summary",
            "tasks": [clean_text] # Return the raw text as a single task so it's not lost
        }

# --- 7. EXPORTABLE EXECUTION FUNCTION ---

def run_ba_agent(project_query: str) -> dict:
    """
    The entry point called by the Orchestrator.
    Returns: {'brd_summary': str, 'tasks': List[str]}
    """
    print(f"--- [BA Agent] Starting Analysis for: {project_query} ---")

    inputs = {"input": project_query, "history": []}
    
    # Use invoke instead of stream to get the final completed state
    final_state = app.invoke(inputs)
    
    # Get the last message which contains the "Final Answer"
    raw_final_output = final_state["history"][-1]
    print(raw_final_output)
    # Structure the data for the Orchestrator
    structured_output = parse_ba_response(raw_final_output)
    
    print(f"--- [BA Agent] Finished. Found {len(structured_output['tasks'])} tasks. ---")
    
    return structured_output

# For testing this file directly:
if __name__ == "__main__":
    result = run_ba_agent("Create a development task list for the Portal-X project")
    print("\nFormatted Result for Orchestrator:")
    print(json.dumps(result, indent=2))
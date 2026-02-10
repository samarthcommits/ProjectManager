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
from agent_prompt_library import PM_PROMPT, BA_PROMPT
import json

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

tools = [retrieve_from_graph]
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
    
    prompt_text = BA_PROMPT.format(
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
# query = "Create a development task list for the Portal-X project based on the BRD."
# print(f"Project Manager initialized for: {query}\n")
# def run_ba_agent(query = ''):
#     inputs = {"input": query, "history": []}
#     output = app.invoke(input=inputs)
#     with open('test_file.txt', 'w') as f:
#         f.write(str(output))
#     return json.loads(output['history'][-1])


import json
import re

# ... (rest of your imports and graph setup) ...

def clean_and_parse_json(text: str):
    """
    Robustly extracts JSON from an LLM response, handling Markdown blocks
    and 'Final Answer:' prefixes.
    """
    # 1. Remove "Final Answer:" prefix if present (case insensitive)
    text = re.sub(r"(?i)^.*?Final Answer:\s*", "", text, flags=re.DOTALL)
    
    # 2. Extract content inside ```json ... ``` or just ``` ... ```
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    
    if json_match:
        text = json_match.group(1)
    else:
        # If no markdown blocks, try to find the first '{' and last '}'
        # This handles cases where the model just dumps the JSON without formatting
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]

    # 3. Parse
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"FAILED TO PARSE JSON: {text[:200]}...") # Print preview for debugging
        # Return a fallback stricture so the Orchestrator doesn't crash
        return {
            "brd_summary": "Error parsing BA output.",
            "modules": [] 
        }

def run_ba_agent(project_query: str) -> dict:
    print(f"--- [BA Agent] Starting Analysis for: {project_query} ---")
    
    inputs = {"input": project_query, "history": []}
    
    # Run the graph
    final_state = app.invoke(inputs)
    
    # Get the raw string from the last message
    raw_final_output = final_state["history"][-1]
    
    # CLEAN and PARSE
    structured_output = clean_and_parse_json(raw_final_output)
    
    # Check if we got valid modules, if not, try to recover or just return empty
    module_count = len(structured_output.get("modules", []))
    print(f"--- [BA Agent] Finished. Extracted {module_count} modules. ---")
    
    return structured_output

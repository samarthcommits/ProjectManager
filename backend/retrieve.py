import json
from typing import List, Optional
from langchain_core.documents import Document
from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser
import os
from dotenv import load_dotenv
from milvus_db import MilvusDB
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
load_dotenv()
from copy import deepcopy
# 5. Push to Neo4j (Same as before)
from langchain_community.graphs import Neo4jGraph
import hashlib
from langchain_community.graphs import Neo4jGraph
from langchain_core.documents import Document
from cipher_queries import retrieval_query, project_query
# Assume 'docs' is your list of chunked documents from the TextSplitter
# and 'custom_graph_transformer' is the function we built in the previous step.
class Graph_Retrieval:
    # 1. Initialize Connection
    graph = Neo4jGraph(url=os.environ['NEO4J_URI'], database='neo4j', username=os.environ['NEO4J_USER'], password=os.environ['NEO4J_PASSWORD'], refresh_schema=False) # Uses env vars for connection
    mil = MilvusDB(collection_name='scalex_collect21', user_name='scalex_test1')
    ret = mil.client.as_retriever()

    # 1. Setup LLM with the OLD "json" format (String, not Schema)

    llm = ChatOllama(
        model="gemma3:27b",
        temperature=0,
        format="json",  # <--- This is key. Old servers accept this string.
        base_url=os.environ['OLLAMA_API_ADDRESS']
    )

    def __init__(self, db_name = None, collection_name = None):
        if db_name and collection_name:
            self.mil = MilvusDB(collection_name=collection_name, user_name=db_name)

    def dense_retrieval(self, query: str, top_k_vectors=3, top_k_final=20):
        print(f"\n--- 1. VECTOR SEARCH (Milvus) for: '{query}' ---")

        milvus_results = self.ret.invoke(query)[:top_k_vectors]
        return milvus_results


    def gravity_retrieval(self, query: str, top_k_vectors=4, top_k_final=20):
        print(f"\n--- 1. GRAPH SEARCH (NEO4J) for: '{query}' ---")

        milvus_results = self.ret.invoke(query)[:top_k_vectors]
    
        seed_indices = [doc.metadata.get('graph_id') for doc in milvus_results]
        # print(f"Found {len(seed_indices)} seed chunks. Indices: {seed_indices}")

        if not seed_indices:
            return "No relevant context found."
        
        # Clean up any old projection first (just in case)
        try:
            # self.graph.query("CALL gds.graph.drop('rag_projection', false)")
            self.graph.query("CALL gds.graph.drop('rag_projection', false) YIELD graphName")
        except Exception:
            pass

        self.graph.query(project_query)
        # print("Graph projected into memory.")

        # --- 3. RUN GRAVITY METHOD (Personalized PageRank) ---
        # print("\n--- 3. RUNNING PPR & FORMATTING ---")
        
        # This query does 3 things:
        # 1. Matches the seed chunks by their 'index' (graph_id)
        # 2. Runs PPR to find the most relevant neighbors
        # 3. Formats the output into text for the LLM
        ppr_query = retrieval_query
        
        results = self.graph.query(ppr_query, params={
            "seed_indices": seed_indices,
            "limit": top_k_final
        })

        # --- 4. CLEANUP & TEXT ASSEMBLY ---
        # self.graph.query("CALL gds.graph.drop('rag_projection', false)")
        self.graph.query("CALL gds.graph.drop('rag_projection', false) YIELD graphName")
        
        final_context = []
        # print(f"Retrieved {len(results)} relevant nodes from Graph.")

        for row in results:
            node_type = row['type'][0] if row['type'] else "Unknown"
            content = row['content']
            score = row['score']
            
            if node_type == "Chunk":
                # It's a text chunk
                final_context.append(f"[SOURCE TEXT] (Score: {score}):\n{content}\n")
            else:
                # It's an Entity (Knowledge Fact)
                rels = [r for r in row['relationships'] if r]
                if rels:
                    facts = "; ".join(rels[:5]) # Limit to 5 facts per entity to save tokens
                    final_context.append(f"[KNOWLEDGE FACT] (Score: {score}): {facts}")

        return "\n".join(final_context)



# r = Graph_Retrieval()
# print(r.dense_retrieval(query='summarize the document about PalTech Prospect Portal'))

# user_query = "Summarize the main themes and organizational goals of the entire document."
# context = gravity_retrieval(user_query)

# print("\n--- FINAL CONTEXT FOR LLM HERE ---")
# print(context)
#--------------------------------------------------------------------------------------------------------------------------#
# Ensure you have your ENV variables set for NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
# graph = Neo4jGraph()
# graph.add_graph_documents(graph_documents)

# ==========================================
# 5. EXECUTE
# ==========================================

# user_query = "What metrics are used to evaluate the model performance?"
# context = gravity_retrieval(user_query)

# print("\n--- FINAL CONTEXT FOR LLM ---")
# print(context)
#-----------------------------------------------------------------------------------------------------------------------------------------#
# Now pass 'context' to Gemma 3 in a standard prompt!

# llm = ChatOllama(
#     model="gemma3:27b",
#     temperature=0,
#     format="json",  # <--- This is key. Old servers accept this string.
#     base_url=os.environ['OLLAMA_API_ADDRESS'],
#     num_ctx=50000
# )
# answer = llm.invoke(f"Answer this: {user_query}\n\nContext:\n{context}. *IMPORTANT* - Also mention the KNOWLEDGE FACTS that seemed relevant to you.")
# print('answer - \n', answer.content)
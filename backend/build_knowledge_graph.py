
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
from langchain_community.graphs import Neo4jGraph
import hashlib
from langchain_community.graphs import Neo4jGraph
from langchain_core.documents import Document

from prompt_library import system_prompt, prune_prompt, mapping_prompt
from cipher_queries import cypher_bridge, cypher_spine

graph = Neo4jGraph(url=os.environ['NEO4J_URI'], database='neo4j', username=os.environ['NEO4J_USER'], password=os.environ['NEO4J_PASSWORD'], refresh_schema=False) # Uses env vars for connection

# 2. Create Constraints (Crucial for performance/deduplication)
# We ensure every Chunk and Entity is unique by its ID
graph.query("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE")
llm = ChatOllama(
    model="gemma3:27b",
    temperature=0,
    format="json",
    base_url=os.environ['OLLAMA_API_ADDRESS'], 
    num_ctx=100000
)


def build_ermap(docs = []):
    print('Building the E-R map...')
    map_prompt = ChatPromptTemplate.from_template(mapping_prompt)

    map_chain = map_prompt | llm | JsonOutputParser()

    all_entities = set()
    all_relationships = set()

    print("Extracting candidates from chunks...")
    for i, doc in enumerate(docs):
        try:
            result = map_chain.invoke({"text": doc.page_content})
            all_entities.update(result.get("entity_types", []))
            all_relationships.update(result.get("relationship_types", []))
            print(f"Chunk {i+1}: Found {len(result.get('entity_types', []))} entity types.")
        except Exception as e:
            print(f"Error on chunk {i+1}: {e}")
    reduce_prompt = ChatPromptTemplate.from_template(prune_prompt)
    reduce_chain = reduce_prompt | llm | JsonOutputParser()
    print("\nConsolidating final schema...")
    final_schema = reduce_chain.invoke({
        "entities": list(all_entities),
        "relationships": list(all_relationships)
    })
    print('Built E-R map!')
    return final_schema

def get_chunks(PDF_PATH = '', chunk_size = 1000, chunk_overlap = 200):
    print('Chunking...')
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, # ~750 tokens
        chunk_overlap=chunk_overlap
    )
    loader = PyPDFLoader(PDF_PATH)
    docs = loader.load_and_split(splitter)
    print(f'{len(docs)} chunks created!')
    return docs

def add_to_milvus(docs = [], db_name = None, collection_name = None):
    print('Adding documents to Milvus Store...')
    for i, k in enumerate(docs):
        k.metadata['graph_id'] = i
        if "pk" in k.metadata:
            k.metadata["source_pk"] = str(k.metadata.pop("pk"))
        else:
            # Provide a default value (e.g., empty string or "00") so the field exists
            k.metadata["source_pk"] = "00"
        

    md = deepcopy(docs[0].metadata)
    md['graph_id'] = -1
    md['source_pk'] = '00'
    if not collection_name or not db_name:
        print('here1')
        mil = MilvusDB(collection_name='graph_78', metadata=md, user_name='graph_rag')
    else:
        print('here2')
        mil = MilvusDB(collection_name=collection_name, metadata=md, user_name=db_name)
    print(docs[:2])
    mil.add_text_docs(texts=docs)
    print('Milvus ingestion complete!')
    return

def add_to_graph(
    documents: List[Document], 
    allowed_nodes: List[str], 
    allowed_rels: List[str]
) -> List[GraphDocument]:
    print('Adding documents to Knowledge graph...')
    extraction_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{text}")
    ])
    chain = extraction_prompt | llm | JsonOutputParser()
    results = []

    for doc in documents:
        try:
            # Invoke the chain
            response = chain.invoke({
                "text": doc.page_content,
                "allowed_nodes": ", ".join(allowed_nodes),
                "allowed_rels": ", ".join(allowed_rels)
            })
                        
            nodes = [
                Node(id=n["id"], type=n["type"]) 
                for n in response.get("nodes", [])
            ]
            
           
            type_map = {n.id: n.type for n in nodes}

            # 3. Parse Relationships using the Map
            relationships = []
            for r in response.get("relationships", []):
                # Look up the type. If the LLM halluncinated a node not in the nodes list, fall back to "Unknown"
                source_type = type_map.get(r["source"], "Unknown")
                target_type = type_map.get(r["target"], "Unknown")
                
                relationships.append(Relationship(
                    source=Node(id=r["source"], type=source_type),
                    target=Node(id=r["target"], type=target_type),
                    type=r["type"]
                ))
                
            results.append(GraphDocument(
                nodes=nodes, 
                relationships=relationships, 
                source=doc
            ))
            print(f"Processed doc: Found {len(nodes)} nodes, {len(relationships)} edges.")
            
        except Exception as e:
            print(f"Error processing document: {e}")
            print('-'*100)
            print(doc)
            print('-'*100)
            print('-'*30, 'END', 30*'-')


    print('Graph Ingestion complete!')
    return results

def connect_chunks_to_entities(docs = [], graph_doc_list = None, allowed_nodes = [], allowed_rels = []):
    print('Connecting chunks to entities...')
    for i, doc in enumerate(docs):
        # --- A. Prepare Chunk Data ---
        print(f'processing chunk {i}')
        chunk_text = doc.page_content
        # Create a unique ID for the chunk based on its content
        chunk_id = hashlib.md5(chunk_text.encode()).hexdigest()
        graph_doc_list = add_to_graph(documents=[doc], allowed_nodes=allowed_nodes, allowed_rels=allowed_rels)
        if graph_doc_list:
            graph.add_graph_documents(graph_doc_list)

        
        
        graph.query(cypher_spine, params={
            "chunk_id": chunk_id,
            "text": chunk_text,
            "index": i
        })
        
        if graph_doc_list:
            gd = graph_doc_list[0]
            
            for node in gd.nodes:

                graph.query(cypher_bridge, params={
                    "chunk_id": chunk_id,
                    "entity_id": node.id
                })
                
        print(f"Processed Chunk {i}: Linked to {len(graph_doc_list[0].nodes) if graph_doc_list else 0} entities.")
        print('Connected chunks to entities!')
    return

def add_to_graph_vectorstore(PDF_PATH = '', milvus_db_name = '', milvus_collection_name = ''):
    docs = get_chunks(PDF_PATH=PDF_PATH, chunk_size=3500, chunk_overlap=200)
    ermap = build_ermap(docs=docs)
    add_to_milvus(docs=docs, db_name=milvus_db_name, collection_name=milvus_collection_name)
    connect_chunks_to_entities(docs=docs, allowed_nodes=ermap['final_entity_labels'], allowed_rels=ermap['final_relationship_types'])
    return 'Ingestion complete!'


if __name__=='__main__':
    PDF_PATH = r"C:\Users\samarth.srivastava\Downloads\brd2.pdf"
    milvus_db_name = 'scalex_test1'
    milvus_collection_name = 'scalex_collect21'
    print(add_to_graph_vectorstore(PDF_PATH=PDF_PATH, milvus_collection_name=milvus_collection_name, milvus_db_name=milvus_db_name))

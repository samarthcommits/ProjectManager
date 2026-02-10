system_prompt = """
You are a Data Scientist extracting information for a Knowledge Graph.
Extract entities (nodes) and relationships (edges) from the text.

1. Nodes should have a 'id' (name), 'type' (label).
2. Relationships should have 'source', 'target', and 'type'.
3. Allowed Node Types: {allowed_nodes}
4. Allowed Relationship Types: {allowed_rels}

Output purely in this JSON format:
{{
  "nodes": [{{"id": "Sarah Chen et al", "type": "Person"}}],
  "relationships": [{{"source": "Sarah Chen et al", "target": "Georgia University", "type": "WORKS_FOR"}}]
}}
"""
prune_prompt = """
You are the Lead Data Architect. Below is a raw list of potential Entity and Relationship types extracted from a document.
Your job is to clean, deduplicate, and standardize this list into a final Schema.

Rules:
1. Merge synonyms (e.g., "SoftwareEngineer" and "Developer" -> "Person" or "Role").
2. Standardize formatting (e.g., "belongs_to" -> "BELONGS_TO").
3. Keep the schema simple (Aim for 15-20 Entity Types max).

Raw Entities: {entities}
Raw Relationships: {relationships}

Output strictly in JSON:
{{
  "final_entity_labels": [],
  "final_relationship_types": []
}}
"""

mapping_prompt = """
You are an expert Ontology Engineer. Analyze the following text chunk.
Identify the top 8-10 distinct ENTITY TYPES (e.g., Person, Project, Algorithm) 
and RELATIONSHIP TYPES (e.g., LEADS, USES, AFFECTS) present in the text.

Do NOT extract specific data (like "Sarah"). Extract the CATEGORIES.

Text Chunk:
{text}

Output strictly in this JSON format:
{{
  "entity_types": ["Type1", "Type2"],
  "relationship_types": ["REL_1", "REL_2"]
}}
"""
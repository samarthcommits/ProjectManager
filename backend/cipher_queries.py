retrieval_query = """
// Step A: Find the Start Nodes (Seeds)
MATCH (s:Chunk) 
WHERE s.index IN $seed_indices
WITH collect(s) AS sourceNodes

// Step B: Run the Algorithm
CALL gds.pageRank.stream('rag_projection', {
maxIterations: 1000,
dampingFactor: 0.85,
sourceNodes: sourceNodes  // The Ink Source
})
YIELD nodeId, score

// Step C: Filter & Format
WITH gds.util.asNode(nodeId) AS n, score
WHERE score > 0.00005  // Noise Filter (Adjust based on your data)

// Step D: Retrieve Context
// Case 1: It's a Chunk -> Get text
// Case 2: It's an Entity -> Get its triplets
OPTIONAL MATCH (n)-[r]->(target)
WHERE NOT n:Chunk AND NOT target:Chunk // Only get Entity-Entity facts

RETURN 
labels(n) AS type,
coalesce(n.text, n.id) AS content,  // Text for Chunks, ID for Entities
score,
collect(
    CASE WHEN target IS NOT NULL 
    THEN n.id + ' ' + type(r) + ' ' + target.id 
    ELSE NULL END
) AS relationships
ORDER BY score DESC
// LIMIT $limit
"""
project_query = """
CALL gds.graph.project(
'rag_projection',    
'*',                  // Load ALL node labels (Chunk, Person, Task, etc.)
'*',                  // Load ALL relationship types
{readConcurrency: 4}
)
"""

cypher_bridge = """
MATCH (c:Chunk {id: $chunk_id})
MATCH (e) WHERE e.id = $entity_id 
MERGE (c)-[:MENTIONS]->(e)
"""

cypher_spine = """
MERGE (c:Chunk {id: $chunk_id})
SET c.text = $text, c.index = $index

WITH c
MATCH (prev:Chunk {index: $index - 1})
WHERE prev IS NOT NULL
MERGE (prev)-[:NEXT]->(c)
"""
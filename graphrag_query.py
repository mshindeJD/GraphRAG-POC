from neo4j import GraphDatabase
from neo4j_config import NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER
import json

class GraphRAGQueryEngine:
    def __init__(self, uri, user, pwd):
        self.driver = GraphDatabase.driver(uri, auth=(user, pwd))

    def close(self):
        if self.driver is not None:
            self.driver.close()

    def search_component(self, search_term):
        # STEP 1: Retrieval (Hybrid/Keyword)
        # Finds the entry point in the graph using the full-text index we created
        query = """
        CALL db.index.fulltext.queryNodes("component_descriptions", $search_term) YIELD node, score
        RETURN node.id AS id, node.name AS name, labels(node)[0] AS type, node.description AS description, score
        LIMIT 1
        """
        with self.driver.session() as session:
            result = session.run(query, search_term=search_term)
            record = result.single()
            if record:
                return dict(record)
            return None

    def analyze_blast_radius(self, component_id):
        # STEP 2: Impact Analysis (Graph Traversal)
        # Finds everything that depends on this component, up to 3 hops away
        query = """
        MATCH (target {id: $id})<-[:HOSTED_ON|CALLS|DEPENDS_ON|READS_WRITES*1..3]-(dependent)
        RETURN DISTINCT dependent.id AS id, 
                        dependent.name AS name, 
                        labels(dependent)[0] AS type
        """
        with self.driver.session() as session:
            result = session.run(query, id=component_id)
            return [dict(record) for record in result]

    def build_llm_prompt(self, user_question, target_node, impacted_nodes):
        # STEP 3: Answer Generation Grounding
        # Formats the graph data into a context block for an LLM
        context = f"Target Component Offline: {target_node['name']} ({target_node['type']})\n"
        context += f"Description: {target_node['description']}\n\n"
        
        context += "Impacted Upstream Dependencies (Blast Radius):\n"
        for node in impacted_nodes:
            context += f"- {node['name']} ({node['type']})\n"

        prompt = f"""
You are an IT Operations AI Assistant. Use the provided Graph Database context to answer the user's question.

### CONTEXT:
{context}

### USER QUESTION:
{user_question}

### INSTRUCTIONS:
Explain the impact of the outage in clear terms. Identify the root infrastructure, the technical applications affected, and the final business services that the customer will notice are down.
"""
        return prompt

if __name__ == "__main__":
    engine = GraphRAGQueryEngine(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    # Simulated User Question
    user_question = "If our primary Azure cluster goes down, what business services will stop working?"
    
    print(f"USER QUESTION: {user_question}\n")

    # 1. Retrieve the node based on keyword extraction (e.g., "Azure cluster")
    print("--- STEP 1: RETRIEVAL ---")
    target = engine.search_component("Azure cluster")
    if target:
        print(f"Found component: {target['name']} (Score: {target['score']})\n")
    else:
        print("Component not found.")
        exit()

    # 2. Traverse the graph for impact analysis
    print("--- STEP 2: IMPACT ANALYSIS ---")
    impacted = engine.analyze_blast_radius(target['id'])
    print(f"Found {len(impacted)} impacted upstream dependencies.\n")

    # 3. Build the prompt for the LLM
    print("--- STEP 3: LLM PROMPT GENERATION ---")
    llm_prompt = engine.build_llm_prompt(user_question, target, impacted)
    print(llm_prompt)

    engine.close()
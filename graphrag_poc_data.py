from neo4j import GraphDatabase
from neo4j_config import NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER

class GraphRAGDataGenerator:
    def __init__(self, uri, user, pwd):
        self.driver = GraphDatabase.driver(uri, auth=(user, pwd))

    def close(self):
        if self.driver is not None:
            self.driver.close()

    def execute_query(self, query, parameters=None):
        with self.driver.session() as session:
            session.run(query, parameters)

    def clear_database(self):
        # Clear existing data for a clean POC
        self.execute_query("MATCH (n) DETACH DELETE n")
        print("Database cleared.")

    def create_cmdb_dependency_graph(self):
        # Creates dummy CMDB data representing IT services, apps, and infrastructure
        cypher_query = """
        // 1. Create Business Services
        CREATE (svc1:BusinessService {
            id: 'BS-001', 
            name: 'Customer Portal', 
            description: 'Main entry point for external customers to manage accounts',
            criticality: 'High'
        })
        CREATE (svc2:BusinessService {
            id: 'BS-002', 
            name: 'Payment Processing', 
            description: 'Handles online transactions and checkout',
            criticality: 'Critical'
        })

        // 2. Create Applications / Microservices
        CREATE (app1:Application {
            id: 'APP-101', 
            name: 'Frontend Web App', 
            technology: 'React',
            description: 'User interface for the customer portal'
        })
        CREATE (app2:Application {
            id: 'APP-102', 
            name: 'Auth API', 
            technology: 'FastAPI',
            description: 'Handles user authentication and JWT tokens'
        })
        CREATE (app3:Application {
            id: 'APP-103', 
            name: 'Order Service', 
            technology: 'Spring Boot',
            description: 'Processes customer orders and connects to payment gateway'
        })

        // 3. Create Databases
        CREATE (db1:Database {
            id: 'DB-201', 
            name: 'User Profiles DB', 
            type: 'PostgreSQL',
            description: 'Relational store for user credentials and metadata'
        })
        CREATE (db2:Database {
            id: 'DB-202', 
            name: 'Transactions Graph', 
            type: 'Neo4j',
            description: 'Graph database storing transaction dependencies and fraud vectors'
        })

        // 4. Create Infrastructure / Servers
        CREATE (srv1:Server {
            id: 'SRV-301', 
            name: 'aks-cluster-prod-01', 
            environment: 'Azure',
            description: 'Primary Kubernetes cluster in Azure East US'
        })

        // 5. Establish Dependencies (The Graph)
        // Services depend on Apps
        CREATE (svc1)-[:DEPENDS_ON {impact_weight: 0.8}]->(app1)
        CREATE (svc1)-[:DEPENDS_ON {impact_weight: 1.0}]->(app2)
        CREATE (svc2)-[:DEPENDS_ON {impact_weight: 1.0}]->(app3)
        CREATE (app1)-[:CALLS]->(app2)
        CREATE (app1)-[:CALLS]->(app3)

        // Apps read/write to Databases
        CREATE (app2)-[:READS_WRITES]->(db1)
        CREATE (app3)-[:READS_WRITES]->(db2)

        // Apps hosted on Infrastructure
        CREATE (app1)-[:HOSTED_ON]->(srv1)
        CREATE (app2)-[:HOSTED_ON]->(srv1)
        CREATE (app3)-[:HOSTED_ON]->(srv1)
        """
        self.execute_query(cypher_query)
        print("Dummy dependency graph created successfully.")

    def create_vector_index(self):
        # In a real GraphRAG setup (like the Azure architecture), you would embed the 'description' 
        # fields and use Neo4j's vector index for hybrid search.
        try:
            index_query = """
            CREATE FULLTEXT INDEX component_descriptions IF NOT EXISTS 
            FOR (n:BusinessService|Application|Database|Server) 
            ON EACH [n.name, n.description]
            """
            self.execute_query(index_query)
            print("Full-text index 'component_descriptions' created for hybrid retrieval.")
        except Exception as e:
            print(f"Index creation note (safe to ignore on free tier if fulltext unsupported): {e}")


if __name__ == "__main__":
    generator = GraphRAGDataGenerator(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    generator.clear_database()
    generator.create_cmdb_dependency_graph()
    generator.create_vector_index()
    
    generator.close()
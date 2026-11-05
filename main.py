from neo4j import GraphDatabase
from neo4j_config import NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER

class Neo4jConnection:
    def __init__(self, uri, user, pwd):
        # Initialize the driver connection
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, pwd))
            self.driver.verify_connectivity()
            print("Successfully connected to Neo4j.")
        except Exception as e:
            print(f"Failed to connect: {e}")
            self.driver = None

    def close(self):
        # Always close the driver when done
        if self.driver is not None:
            self.driver.close()

    def execute_query(self, query, parameters=None, db_name="neo4j"):
        if self.driver is None:
            return None
            
        # Explicitly declare which database to connect to
        with self.driver.session(database=db_name) as session:
            result = session.run(query, parameters)
            return [record for record in result]

if __name__ == "__main__":
    # Instantiate connection
    db = Neo4jConnection(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    # Example: Run a test query to count all nodes
    test_query = "MATCH (n) RETURN count(n) AS node_count"
    
    records = db.execute_query(test_query)
    
    if records:
        print(f"Total nodes in database: {records[0]['node_count']}")

    # Clean up
    db.close()
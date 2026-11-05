from neo4j import GraphDatabase
from neo4j_config import NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER

class ServiceNowMetadataGraph:
    def __init__(self, uri, user, pwd):
        self.driver = GraphDatabase.driver(uri, auth=(user, pwd))

    def execute_query(self, query, parameters=None):
        with self.driver.session() as session:
            session.run(query, parameters)

    def clear_database(self):
        self.execute_query("MATCH (n) DETACH DELETE n")
        print("Database cleared for ServiceNow POC.")

    def create_metadata_graph(self):
         
        // 1. Create Tables
        CREATE (t_task:Table {name: 'task', label: 'Task', sys_id: 'sys_1001'})
        CREATE (t_inc:Table {name: 'incident', label: 'Incident', sys_id: 'sys_1002'})
        CREATE (t_inc)-[:EXTENDS]->(t_task)

        // 2. Create Columns (Schema)
        CREATE (c_state:Column {name: 'state', type: 'integer', label: 'State', sys_id: 'sys_2001'})
        CREATE (c_cat:Column {name: 'category', type: 'choice', label: 'Category', sys_id: 'sys_2002'})
        CREATE (c_caller:Column {name: 'caller_id', type: 'reference', label: 'Caller', sys_id: 'sys_2003'})
        
        // Link Columns to Table
        CREATE (t_inc)-[:HAS_COLUMN]->(c_state)
        CREATE (t_inc)-[:HAS_COLUMN]->(c_cat)
        CREATE (t_inc)-[:HAS_COLUMN]->(c_caller)

        // 3. Create Downstream ServiceNow Assets (Impact Nodes)
        CREATE (br_cat:BusinessRule {
            name: 'Assign Routing by Category', 
            type: 'before_insert', 
            sys_id: 'br_3001',
            description: 'Sets assignment group based on incident category.'
        })
        CREATE (flow_esc:Flow {
            name: 'P1 Incident Escalation', 
            status: 'published', 
            sys_id: 'fl_3002',
            description: 'Triggers when State changes to Work in Progress for high priority.'
        })
        CREATE (cs_state:ClientScript {
            name: 'Make State ReadOnly', 
            type: 'onLoad', 
            sys_id: 'cs_3003',
            description: 'Locks the state field for non-itil users.'
        })
        CREATE (rep_cat:Report {
            name: 'Monthly Incidents by Category', 
            table: 'incident', 
            sys_id: 'rp_3004',
            description: 'Pie chart grouping incidents by category.'
        })
        CREATE (api_jira:Integration {
            name: 'Jira Bi-Directional Sync', 
            type: 'REST API', 
            sys_id: 'int_3005',
            description: 'Pushes caller_id and state to Jira payloads.'
        })

        // 4. Establish Dependencies (The Blast Radius Edges)
        CREATE (br_cat)-[:DEPENDS_ON {usage: 'script_condition'}]->(c_cat)
        CREATE (rep_cat)-[:DEPENDS_ON {usage: 'group_by_field'}]->(c_cat)
        
        CREATE (flow_esc)-[:DEPENDS_ON {usage: 'trigger_condition'}]->(c_state)
        CREATE (cs_state)-[:DEPENDS_ON {usage: 'g_form.setReadOnly'}]->(c_state)
        CREATE (api_jira)-[:DEPENDS_ON {usage: 'payload_mapping'}]->(c_state)
        
        CREATE (api_jira)-[:DEPENDS_ON {usage: 'payload_mapping'}]->(c_caller)
        """
        self.execute_query(cypher_query)
        print("ServiceNow schema and downstream dependencies created successfully.")

    def create_search_index(self):
        try:
            index_query = """
            CREATE FULLTEXT INDEX snow_metadata IF NOT EXISTS 
            FOR (n:Table|Column|BusinessRule|Flow|ClientScript|Report|Integration) 
            ON EACH [n.name, n.label, n.description]
            """
            self.execute_query(index_query)
            print("Full-text index 'snow_metadata' created.")
        except Exception as e:
            pass

    def close(self):
        if self.driver is not None:
            self.driver.close()

if __name__ == "__main__":
    snow_graph = ServiceNowMetadataGraph(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    snow_graph.clear_database()
    snow_graph.create_metadata_graph()
    snow_graph.create_search_index()
    snow_graph.close()
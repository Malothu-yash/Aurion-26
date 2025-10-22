"""
Helper script to query your Neo4j knowledge graph.
Use this to explore what AURION has learned about you!
"""
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

def query_neo4j(cypher_query: str):
    """Execute a Cypher query and print results."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        result = session.run(cypher_query)
        records = list(result)
        
        if not records:
            print("No results found.")
            return
        
        print(f"\n📊 Found {len(records)} result(s):\n")
        for i, record in enumerate(records, 1):
            print(f"{i}. {dict(record)}")
    
    driver.close()

def main():
    print("""
    🔍 NEO4J KNOWLEDGE GRAPH EXPLORER
    ===================================
    
    This tool helps you explore the semantic memory AURION has built.
    """)
    
    print("\n🎯 Common Queries:\n")
    print("1. View all relationships")
    print("2. View all people")
    print("3. View all facts about a specific user")
    print("4. View all cities")
    print("5. View all hobbies")
    print("6. Custom query")
    print("0. Exit")
    
    queries = {
        "1": "MATCH (n)-[r]->(m) RETURN n.name AS from, type(r) AS relationship, m.name AS to LIMIT 50",
        "2": "MATCH (p:Person) RETURN p.name AS person",
        "3": None,  # Will ask for user_id
        "4": "MATCH (c:City) RETURN c.name AS city",
        "5": "MATCH (h:Hobby) RETURN h.name AS hobby"
    }
    
    while True:
        choice = input("\nSelect option (0-6): ").strip()
        
        if choice == "0":
            print("Goodbye! 👋")
            break
        
        if choice == "3":
            user_id = input("Enter user/conversation ID (e.g., semantic-test-123): ").strip()
            query = f"MATCH (u:User {{id: '{user_id}'}})-[r]->(n) RETURN type(r) AS relationship, n.name AS fact"
        elif choice == "6":
            query = input("Enter your Cypher query: ").strip()
        elif choice in queries:
            query = queries[choice]
        else:
            print("❌ Invalid choice. Try again.")
            continue
        
        print(f"\n🔎 Running query: {query}\n")
        print("="*70)
        
        try:
            query_neo4j(query)
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("="*70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting... 👋")

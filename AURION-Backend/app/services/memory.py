
# app/services/memory.py
# This file handles all communication with our memory databases.

import redis.asyncio as redis  # Async redis client
from pinecone import Pinecone, ServerlessSpec
from app.core.config import settings
import json
from neo4j import AsyncGraphDatabase
import asyncio

# --- 1. Redis Client ---
# We will create a "connection pool" that our app can share.
# We'll initialize it as None and connect during the app startup.
redis_pool = None

async def init_redis_pool():
    """
    Initializes the Redis connection pool.
    This is called once when the FastAPI app starts.
    """
    global redis_pool
    try:
        # Use the REDIS_URL from your .env if you have it
        if settings.REDIS_URL:
            # --- THIS IS THE FIX ---
            # We explicitly create a ConnectionPool from the URL.
            redis_pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL, 
                decode_responses=True
            )
        else:
            # Fallback to individual host, port, password
            redis_pool = redis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                decode_responses=True # So we get strings back, not bytes
            )
        
        # Test the connection
        # This part will now work correctly
        async with redis.Redis(connection_pool=redis_pool) as r:
            await r.ping()
        print("Redis connection pool initialized successfully.")
    except Exception as e:
        print(f"Error initializing Redis pool: {e}")
        redis_pool = None

async def close_redis_pool():
    """
    Closes the Redis connection pool.
    This is called once when the FastAPI app shuts down.
    """
    if redis_pool:
        await redis_pool.disconnect()
        print("Redis connection pool closed.")

async def get_chat_history(conversation_id: str, limit: int = 10) -> list[dict]:
    """
    Gets the most recent chat history for a conversation from Redis.
    We store history as a list of JSON-encoded messages.
    """
    # Be resilient in environments without Redis
    if not redis_pool:
        # Return empty history rather than raising to avoid 500s
        return []
    
    key = f"chat_history:{conversation_id}"
    try:
        async with redis.Redis(connection_pool=redis_pool) as r:
            # Get the last 'limit' items from the list
            messages_str = await r.lrange(key, -limit, -1)
            # Decode the JSON strings back into dictionaries
            return [json.loads(msg) for msg in messages_str]
    except Exception as e:
        print(f"Error getting chat history from Redis: {e}")
        return []

async def add_to_chat_history(conversation_id: str, role: str, text: str):
    """
    Adds a new message to the chat history in Redis.
    """
    # Be resilient in environments without Redis
    if not redis_pool:
        # No-op if Redis isn't configured
        return
    
    key = f"chat_history:{conversation_id}"
    message = json.dumps({"role": role, "content": text})
    
    try:
        async with redis.Redis(connection_pool=redis_pool) as r:
            await r.rpush(key, message) # Add to the right side of the list
            await r.ltrim(key, -50, -1) # Keep only the last 50 messages
    except Exception as e:
        print(f"Error adding to chat history in Redis: {e}")


# --- 2. Pinecone Client ---
pinecone_index = None

def init_pinecone():
    """
    Initializes the Pinecone client and index.
    This is a synchronous function, so we call it normally
    during the app startup.
    """
    global pinecone_index
    try:
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        index_name = settings.PINECONE_INDEX_NAME
        
        # Check if the index already exists
        if index_name not in pc.list_indexes().names():
            # If not, create it
            print(f"Pinecone index '{index_name}' not found. Creating...")
            pc.create_index(
                name=index_name,
                dimension=3072, # IMPORTANT: Matches text-embedding-3-large
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1' # Use a free tier region
                )
            )
            print("Pinecone index created successfully.")
        else:
            print(f"Pinecone index '{index_name}' found.")
            
        pinecone_index = pc.Index(index_name)
        print("Pinecone client initialized successfully.")
        
    except Exception as e:
        print(f"Error initializing Pinecone: {e}")
        pinecone_index = None

async def upsert_to_pinecone(vector_id: str, vector: list[float], metadata: dict):
    """
    Upserts (updates or inserts) a vector into our Pinecone index.
    """
    if not pinecone_index:
        # No-op if Pinecone isn't configured
        return
    
    try:
        # Pinecone's async upsert is a bit different,
        # for simplicity we can run the sync upsert in a thread
        # but the client itself supports async.
        # Let's keep it simple for now.
        pinecone_index.upsert(
            vectors=[{
                "id": vector_id,
                "values": vector,
                "metadata": metadata
            }],
            namespace="aurion_namespace"
        )
    except Exception as e:
        print(f"Error upserting to Pinecone: {e}")
        raise

async def query_pinecone(vector: list[float], top_k: int = 3) -> list[dict]:
    """
    Queries Pinecone to find the most similar memories.
    """
    if not pinecone_index:
        # Return no matches if Pinecone isn't configured
        return []
        
    try:
        results = pinecone_index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
            namespace="aurion_namespace"
        )
        # Return a list of the metadata from the matches
        return [match['metadata'] for match in results['matches']]
    except Exception as e:
        print(f"Error querying Pinecone: {e}")
        return []


async def get_recent_conversations(conversation_id: str, days: int = 7) -> str:
    """
    Fetches all recent memories from Pinecone for a user.
    Used for memory consolidation to find patterns.
    
    Args:
        conversation_id: The user's conversation ID
        days: Number of days to look back (default 7 for weekly consolidation)
    
    Returns:
        A formatted transcript of recent conversations
    """
    if not pinecone_index:
        print("Pinecone index not initialized.")
        return ""
    
    try:
        from app.services import ai_clients
        
        # We query with a generic embedding to get conversations
        # This is a workaround - in production you'd use timestamp filtering
        query_embedding = await ai_clients.get_embedding("conversation history")
        
        results = pinecone_index.query(
            vector=query_embedding,
            top_k=100,  # Get the last 100 interactions
            filter={"conversation_id": {"$eq": conversation_id}},
            include_metadata=True,
            namespace="aurion_namespace"
        )
        
        if not results['matches']:
            print(f"No conversations found for {conversation_id}")
            return ""
        
        # Combine into a single transcript
        transcript_lines = []
        for match in results['matches']:
            metadata = match['metadata']
            user_query = metadata.get('user_query', '')
            model_response = metadata.get('model_response', '')
            timestamp = metadata.get('timestamp', '')
            
            if user_query and model_response:
                transcript_lines.append(f"[{timestamp}]")
                transcript_lines.append(f"User: {user_query}")
                transcript_lines.append(f"Assistant: {model_response}")
                transcript_lines.append("")  # Empty line for readability
        
        transcript = "\n".join(transcript_lines)
        print(f"Retrieved {len(results['matches'])} conversation snippets for consolidation")
        return transcript
        
    except Exception as e:
        print(f"Error fetching recent conversations: {e}")
        return ""


# --- 3. Neo4j Client (Semantic Memory) ---
neo4j_driver = None

def init_neo4j():
    """
    Initializes the Neo4j Async Driver.
    This is a synchronous function called at startup.
    """
    global neo4j_driver
    try:
        uri = settings.NEO4J_URI
        user = settings.NEO4J_USER
        password = settings.NEO4J_PASSWORD
        neo4j_driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        print("Neo4j connection initialized successfully.")
    except Exception as e:
        print(f"Error initializing Neo4j: {e}")
        neo4j_driver = None

async def close_neo4j():
    """
    Closes the Neo4j driver connection.
    Called at shutdown.
    """
    if neo4j_driver:
        await neo4j_driver.close()
        print("Neo4j connection closed.")

def get_neo4j_driver():
    """
    Returns the Neo4j driver instance.
    Use this function to safely access the driver from other modules.
    """
    return neo4j_driver

async def add_relationships_to_graph(cypher_query: str):
    """
    Executes a Cypher query to write relationships to the graph.
    This is the function our background task will call.
    """
    if not neo4j_driver:
        print("Neo4j driver not initialized, skipping graph update.")
        return

    try:
        # We use "async with" to properly manage the session
        async with neo4j_driver.session() as session:
            # We use a transaction to ensure the query either
            # fully succeeds or fully fails.
            async with session.begin_transaction() as tx:
                await tx.run(cypher_query)
                await tx.commit()
        print("Neo4j semantic memory updated.")
    except Exception as e:
        print(f"Error updating Neo4j graph: {e}")

async def get_facts_from_graph(conversation_id: str) -> list[str]:
    """
    Fetches all known facts about a user from the Neo4j graph.
    Returns a list of human-readable fact strings.
    
    Example return:
    ["User HAS_BOSS Vamshi", "User LIVES_IN Hyderabad", "User LIKES Cricket"]
    """
    if not neo4j_driver:
        print("Neo4j driver not initialized, returning empty facts.")
        return []

    # Simplified query - only check for 'name' property which is the standard property
    # This avoids Neo4j warnings about non-existent properties
    query = f"""
    MATCH (u:User {{id: '{conversation_id}'}})-[r]->(n)
    WHERE n.name IS NOT NULL
    RETURN "User " + type(r) + " " + n.name AS fact
    """
    
    try:
        async with neo4j_driver.session() as session:
            result = await session.run(query)
            facts = [record["fact"] async for record in result if record["fact"].strip()]
            print(f"✅ Neo4j: Fetched {len(facts)} facts for {conversation_id}")
            return facts
    except Exception as e:
        print(f"Error fetching facts from Neo4j: {e}")
        return []




from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv(dotenv_path=".env")

uri = os.getenv("mongo_uri")
db_name = os.getenv("mongo_db_name")

print(f"Testing MongoDB connection to URI: {uri}")

client = MongoClient(uri)
try:
    client.admin.command('ping')
    print("MongoDB connection successful!")
except Exception as e:
    print("MongoDB connection failed:", e)

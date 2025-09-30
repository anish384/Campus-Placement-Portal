from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
try:
    client = MongoClient(os.getenv('MONGO_URI'), serverSelectionTimeoutMS=5000)
    # Force a connection
    client.server_info()
    print("Successfully connected to MongoDB!")
    print("Available databases:", client.list_database_names())
except Exception as e:
    print("Error connecting to MongoDB:", str(e))
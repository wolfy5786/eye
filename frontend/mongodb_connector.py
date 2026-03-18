from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(
    "mongodb+srv://reachtoatharv_db_user:vbOtyCBc7fEHxDx8@cluster0.ljy4nay.mongodb.net/?appName=Cluster0"
)
db = client["RUCHackathon"]

from pymongo import MongoClient

def database(client):
    client = MongoClient(client)

    db = client['daydrift']
    return db



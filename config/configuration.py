from dotenv import load_dotenv
import os
from datetime import timedelta

load_dotenv()

username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")

class Config:
    DEBUG = True
    VERSION = 'v1'
    PORT = 5000
    SECRET_KEY = 'asfasdhkl2kjhasil3jb'
    JWT_SECRET_KEY = 'your-jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES= timedelta(hours=1)
class Development(Config):
    HOST = '127.0.0.1'
    DATABASE_CLIENT='mongodb://localhost:27017/'
    # If you have specific mail settings for development, add them here

class Production(Config):
    DEBUG = False
    VERSION = 'v1'
    HOST = '0.0.0.0'
    DATABASE_CLIENT=f'mongodb+srv://{username}:{password}@cluster0.njun9ub.mongodb.net/?retryWrites=true&w=majority'

    # If you have specific mail settings for production, add them here

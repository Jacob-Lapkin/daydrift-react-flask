from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    DEBUG = True
    VERSION = 'v1'
    PORT = 5000
    SECRET_KEY = 'aslkjhas3'
    JWT_SECRET_KEY = 'your-jwt-secret-key'

class Development(Config):
    HOST = '127.0.0.1'
    # If you have specific mail settings for development, add them here

class Production(Config):
    DEBUG = False
    VERSION = 'v1'
    HOST = '0.0.0.0'
    # If you have specific mail settings for production, add them here

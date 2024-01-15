import os
import binascii

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or binascii.hexlify(os.urandom(32)).decode('utf-8')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or 'your_openai_api_key'

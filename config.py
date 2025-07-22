import os
from dotenv import load_dotenv
# config.py
# Loads environment variables and sets up Flask configuration:
# - SECRET_KEY for session security
# - PostgreSQL database URI for SQLAlchemy
# - Upload limits and folder paths
# - Automatically creates required directories for repos and uploads


load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:pass@localhost/minigithub'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REPOS_PATH = os.environ.get('REPOS_PATH') or './repos'
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or './static/uploads'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH') or 16 * 1024 * 1024)  # 16MB
    
    # Ensure directories exist
os.makedirs(Config.REPOS_PATH, exist_ok=True)
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
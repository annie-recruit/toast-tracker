import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Notion API Configuration
    NOTION_TOKEN = os.getenv('NOTION_TOKEN')
    NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')
    
    # OpenAI API Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    
    # Database Configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'productivity_tracker.db')
    
    # Notification Settings
    NOTIFICATION_ENABLED = os.getenv('NOTIFICATION_ENABLED', 'true').lower() == 'true'
    NOTIFICATION_SOUND = os.getenv('NOTIFICATION_SOUND', 'true').lower() == 'true'
    NOTIFICATION_LEAD_TIME = int(os.getenv('NOTIFICATION_LEAD_TIME', '5'))  # minutes

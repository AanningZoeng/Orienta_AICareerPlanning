"""
Configuration management for SpoonOS agents and LLM providers.
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration."""
    
    # LLM Provider Configuration
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek")
    MODEL_NAME = os.getenv("MODEL_NAME", "deepseek-chat")
    
    # API Server Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 5000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    @classmethod
    def validate(cls):
        """Validate that required API keys are present."""
        if cls.LLM_PROVIDER == "deepseek" and not cls.DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY is required when using DeepSeek provider")
        elif cls.LLM_PROVIDER == "gemini" and not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required when using Gemini provider")

"""
Configuration management for SpoonOS agents and LLM providers.
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# config.py 在 backend/ 目录，项目根目录在上一层
ROOT_DIR = Path(__file__).resolve().parent.parent  # backend/config.py -> Orienta_AICareerPlanning/
env_path = ROOT_DIR / ".env"

# Debug output
if env_path.exists():
    print(f"✅ Found .env at: {env_path}")
else:
    print(f"❌ No .env file at: {env_path}")

# Load with override=True to ensure .env values take precedence
load_dotenv(dotenv_path=env_path, override=True)

class Config:
    """Application configuration."""
    
    # LLM Provider Configuration
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Prefer explicit env `LLM_PROVIDER`, then `DEFAULT_LLM_PROVIDER` from .env,
    # finally fall back to `gemini` as the safe default for this project.
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", os.getenv("DEFAULT_LLM_PROVIDER", "gemini"))
    MODEL_NAME = os.getenv("MODEL_NAME", os.getenv("DEFAULT_MODEL", "gemini-2.5-pro"))
    
    # API Server Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 5000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    # Optional LLM call parameters
    # Set MAX_TOKENS to a safe default; providers have different limits.
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", 2048))
    
    @classmethod
    def validate(cls):
        """Validate that required API keys are present."""
        if cls.LLM_PROVIDER == "deepseek" and not cls.DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY is required when using DeepSeek provider")
        elif cls.LLM_PROVIDER == "gemini" and not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required when using Gemini provider")

    @classmethod
    def get_safe_max_tokens(cls, provider: str = None) -> int:
        """Return a provider-safe max_tokens value (clamped where necessary).

        Currently clamps DeepSeek to [1, 8192]. Other providers fall back to the
        configured MAX_TOKENS but are coerced into a sensible integer.
        """
        prov = provider or cls.LLM_PROVIDER
        try:
            val = int(cls.MAX_TOKENS)
        except Exception:
            val = 2048

        # Provider specific clamps
        if prov == "deepseek":
            return max(1, min(val, 8192))

        # Generic safe range
        return max(1, min(val, 65536))

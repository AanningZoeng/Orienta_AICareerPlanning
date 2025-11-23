"""尝试直接传递API key给ChatBot"""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.config import Config

print("Testing different initialization methods for SpoonAI ChatBot")
print("="*70)

api_key = Config.GEMINI_API_KEY
print(f"API Key: {api_key[:20]}..." if api_key else "NO KEY")

from spoon_ai.chat import ChatBot
import asyncio
import inspect

# 检查ChatBot的构造函数签名
print("\nChatBot constructor signature:")
sig = inspect.signature(ChatBot.__init__)
print(sig)

print("\n" + "="*70)
print("Method 1: 通过环境变量")
print("="*70)
os.environ["GEMINI_API_KEY"] = api_key
try:
    llm1 = ChatBot(llm_provider="gemini", model_name="gemini-2.5-pro")
    response1 = asyncio.run(llm1.chat("Say OK"))
    print(f"✅ Method 1 SUCCESS: {response1}")
except Exception as e:
    print(f"❌ Method 1 FAILED: {e}")

print("\n" + "="*70)
print("Method 2: 传递 api_key 参数")
print("="*70)
try:
    llm2 = ChatBot(llm_provider="gemini", model_name="gemini-2.5-pro", api_key=api_key)
    response2 = asyncio.run(llm2.chat("Say OK"))
    print(f"✅ Method 2 SUCCESS: {response2}")
except Exception as e:
    print(f"❌ Method 2 FAILED: {e}")

print("\n" + "="*70)
print("Method 3: 传递 config 字典")
print("="*70)
try:
    config = {
        "api_key": api_key,
        "model_name": "gemini-2.5-pro"
    }
    llm3 = ChatBot(llm_provider="gemini", config=config)
    response3 = asyncio.run(llm3.chat("Say OK"))
    print(f"✅ Method 3 SUCCESS: {response3}")
except Exception as e:
    print(f"❌ Method 3 FAILED: {e}")

print("\n" + "="*70)
print("Method 4: 使用 kwargs")
print("="*70)
try:
    llm4 = ChatBot(
        llm_provider="gemini",
        model_name="gemini-2.5-pro",
        gemini_api_key=api_key
    )
    response4 = asyncio.run(llm4.chat("Say OK"))
    print(f"✅ Method 4 SUCCESS: {response4}")
except Exception as e:
    print(f"❌ Method 4 FAILED: {e}")

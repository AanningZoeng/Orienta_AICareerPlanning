"""检查 Config 读取的值"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.config import Config

print("="*60)
print("检查 Config 读取的值")
print("="*60)

print(f"\nGEMINI_API_KEY 完整值:")
print(f"  {Config.GEMINI_API_KEY}")

print(f"\n前30字符: {Config.GEMINI_API_KEY[:30]}...")
print(f"\nLLM_PROVIDER: {Config.LLM_PROVIDER}")
print(f"MODEL_NAME: {Config.MODEL_NAME}")
print(f"MAX_TOKENS: {Config.MAX_TOKENS}")

print("\n检查环境变量:")
print(f"  os.environ.get('GEMINI_API_KEY'): {os.environ.get('GEMINI_API_KEY', 'NOT SET')}")

print("\n检查 .env 文件路径:")
from pathlib import Path
# .env 文件在项目根目录，不是在 backend/ 目录
env_path = Path(__file__).parent.parent / '.env'
print(f"  {env_path}")
print(f"  存在: {env_path.exists()}")

if env_path.exists():
    print(f"\n.env 文件内容:")
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            if 'GEMINI_API_KEY' in line and not line.strip().startswith('#'):
                print(f"  {line.strip()}")

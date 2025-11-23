"""检查环境变量的来源"""
import sys
import os

print("="*60)
print("检查 GEMINI_API_KEY 的来源")
print("="*60)

# 在加载 .env 之前检查系统环境变量
print("\n1. 系统环境变量 (加载 .env 之前):")
print(f"   GEMINI_API_KEY: {os.environ.get('GEMINI_API_KEY', 'NOT SET')}")

# 现在加载 .env
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from backend.config import Config

print("\n2. Config 对象读取的值:")
print(f"   Config.GEMINI_API_KEY: {Config.GEMINI_API_KEY}")
print(f"   前30字符: {Config.GEMINI_API_KEY[:30] if Config.GEMINI_API_KEY else 'EMPTY'}...")

print("\n3. 系统环境变量 (加载 .env 之后):")
print(f"   GEMINI_API_KEY: {os.environ.get('GEMINI_API_KEY', 'NOT SET')}")

print("\n4. 读取 .env 文件内容:")
from pathlib import Path
env_path = Path(__file__).parent.parent / 'backend' / '.env'
with open(env_path, 'r', encoding='utf-8') as f:
    for line in f:
        if 'GEMINI_API_KEY' in line and not line.strip().startswith('#'):
            print(f"   {line.strip()}")

print("\n" + "="*60)
print("结论:")
if os.environ.get('GEMINI_API_KEY') != Config.GEMINI_API_KEY:
    print("⚠️  系统环境变量和 Config 值不同！")
    print("   可能存在系统级环境变量覆盖了 .env 文件")
else:
    print("✅ 系统环境变量和 Config 值一致")

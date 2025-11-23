"""测试API key的完整流程"""
import sys
import os
from pathlib import Path

print("="*70)
print("Step 1: 检查导入前的环境变量")
print("="*70)
print(f"GEMINI_API_KEY (before import): {os.environ.get('GEMINI_API_KEY', 'NOT SET')}")

print("\n" + "="*70)
print("Step 2: 导入 Config")
print("="*70)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.config import Config
print(f"Config.GEMINI_API_KEY: {Config.GEMINI_API_KEY[:30]}..." if Config.GEMINI_API_KEY else "EMPTY")
print(f"GEMINI_API_KEY (after Config): {os.environ.get('GEMINI_API_KEY', 'NOT SET')}")

print("\n" + "="*70)
print("Step 3: 显式设置 os.environ")
print("="*70)
if Config.GEMINI_API_KEY:
    os.environ["GEMINI_API_KEY"] = Config.GEMINI_API_KEY
    print(f"✅ Set os.environ['GEMINI_API_KEY'] = {Config.GEMINI_API_KEY[:30]}...")
    print(f"GEMINI_API_KEY (after set): {os.environ.get('GEMINI_API_KEY', 'NOT SET')[:30]}...")

print("\n" + "="*70)
print("Step 4: 导入 SpoonAI")
print("="*70)
try:
    from spoon_ai.chat import ChatBot
    print("✅ SpoonAI imported successfully")
    
    print("\n" + "="*70)
    print("Step 5: 创建 ChatBot")
    print("="*70)
    print(f"Provider: {Config.LLM_PROVIDER}")
    print(f"Model: {Config.MODEL_NAME}")
    print(f"GEMINI_API_KEY in os.environ: {'YES' if 'GEMINI_API_KEY' in os.environ else 'NO'}")
    
    llm = ChatBot(llm_provider=Config.LLM_PROVIDER, model_name=Config.MODEL_NAME)
    print("✅ ChatBot created successfully")
    print(f"ChatBot config: {getattr(llm, 'config', 'N/A')}")
    
    print("\n" + "="*70)
    print("Step 6: 测试简单调用")
    print("="*70)
    import asyncio
    
    async def test_call():
        try:
            response = await llm.chat("Say 'Hello'")
            print(f"✅ LLM Response: {response}")
            return True
        except Exception as e:
            print(f"❌ LLM Call Failed: {e}")
            return False
    
    result = asyncio.run(test_call())
    
    if result:
        print("\n✅✅✅ All tests passed!")
    else:
        print("\n❌ LLM call failed - API key issue")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

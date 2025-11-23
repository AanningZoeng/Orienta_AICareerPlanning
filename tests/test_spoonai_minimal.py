"""最小化测试 - 找出SpoonAI到底需要什么"""
import os
import sys
from pathlib import Path

# Step 1: 设置环境
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("Step 1: 加载 Config")
from backend.config import Config
print(f"✅ Config.GEMINI_API_KEY = {Config.GEMINI_API_KEY[:20]}..." if Config.GEMINI_API_KEY else "❌ EMPTY")

# Step 2: 显式设置所有可能的环境变量名
print("\nStep 2: 设置环境变量（尝试所有可能的名称）")
api_key = Config.GEMINI_API_KEY
if api_key:
    os.environ["GEMINI_API_KEY"] = api_key
    os.environ["GOOGLE_API_KEY"] = api_key  # 有些库使用这个
    os.environ["GENAI_API_KEY"] = api_key   # 或者这个
    print(f"✅ Set GEMINI_API_KEY")
    print(f"✅ Set GOOGLE_API_KEY")
    print(f"✅ Set GENAI_API_KEY")

# Step 3: 打印当前所有相关的环境变量
print("\nStep 3: 当前环境变量状态")
for key in ["GEMINI_API_KEY", "GOOGLE_API_KEY", "GENAI_API_KEY", "LLM_PROVIDER", "MODEL_NAME"]:
    val = os.environ.get(key, "NOT SET")
    if "KEY" in key and val != "NOT SET":
        print(f"{key} = {val[:20]}...")
    else:
        print(f"{key} = {val}")

# Step 4: 导入SpoonAI并测试
print("\nStep 4: 导入 SpoonAI")
try:
    from spoon_ai.chat import ChatBot
    from spoon_ai.agents import SpoonReactAI
    print("✅ SpoonAI imported")
    
    print("\nStep 5: 创建 ChatBot")
    llm = ChatBot(llm_provider="gemini", model_name="gemini-2.5-pro")
    print(f"✅ ChatBot created")
    print(f"   Type: {type(llm)}")
    print(f"   Attributes: {dir(llm)}")
    
    # 检查 ChatBot 内部配置
    if hasattr(llm, '_api_key'):
        print(f"   _api_key: {'SET' if llm._api_key else 'NOT SET'}")
    if hasattr(llm, 'api_key'):
        print(f"   api_key: {'SET' if llm.api_key else 'NOT SET'}")
    if hasattr(llm, 'config'):
        print(f"   config: {llm.config}")
        
    print("\nStep 6: 测试简单调用")
    import asyncio
    
    async def test():
        try:
            response = await llm.chat("Reply with just the word 'OK'")
            print(f"✅ SUCCESS! Response: {response}")
            return True
        except Exception as e:
            print(f"❌ FAILED: {e}")
            
            # 详细错误信息
            print("\n详细错误追踪:")
            import traceback
            traceback.print_exc()
            
            # 检查错误类型
            error_msg = str(e).lower()
            if "authentication" in error_msg or "api key" in error_msg:
                print("\n🔍 这是API key认证问题")
                print("可能原因:")
                print("1. SpoonAI使用了不同的环境变量名")
                print("2. API key没有正确传递到底层库")
                print("3. ChatBot初始化时没有读取环境变量")
            return False
    
    result = asyncio.run(test())
    
    if not result:
        print("\n" + "="*70)
        print("调试建议:")
        print("="*70)
        print("1. 检查SpoonAI源码，看它如何读取API key")
        print("2. 尝试直接传递api_key参数给ChatBot()")
        print("3. 检查是否需要在ChatBot初始化时显式传递配置")
        
except Exception as e:
    print(f"❌ 导入或初始化失败: {e}")
    import traceback
    traceback.print_exc()

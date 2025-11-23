"""诊断SpoonAI ChatBot的API key认证问题"""
import sys
import os
from pathlib import Path
import asyncio

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("="*80)
print("SpoonAI API Key 认证诊断工具")
print("="*80)

# Step 1: 加载配置
print("\n[Step 1] 加载 Config")
from backend.config import Config
print(f"✅ Config.GEMINI_API_KEY = {Config.GEMINI_API_KEY[:30]}..." if Config.GEMINI_API_KEY else "❌ EMPTY")
print(f"✅ Config.LLM_PROVIDER = {Config.LLM_PROVIDER}")
print(f"✅ Config.MODEL_NAME = {Config.MODEL_NAME}")

# Step 2: 设置环境变量
print("\n[Step 2] 设置环境变量")
os.environ["GEMINI_API_KEY"] = Config.GEMINI_API_KEY
print(f"✅ os.environ['GEMINI_API_KEY'] = {os.environ.get('GEMINI_API_KEY', '')[:30]}...")

# Step 3: 导入 SpoonAI
print("\n[Step 3] 导入 SpoonAI")
try:
    from spoon_ai.chat import ChatBot
    print("✅ SpoonAI imported successfully")
except Exception as e:
    print(f"❌ Failed to import SpoonAI: {e}")
    sys.exit(1)

# Step 4: 检查 ChatBot 构造函数签名
print("\n[Step 4] 检查 ChatBot 构造函数")
import inspect
sig = inspect.signature(ChatBot.__init__)
print(f"ChatBot.__init__ signature: {sig}")
params = list(sig.parameters.keys())
print(f"Parameters: {params}")
print(f"Accepts 'api_key'? {'api_key' in params}")

# Step 5: 测试不同的初始化方法
print("\n[Step 5] 测试不同的初始化方法")

test_results = {}

# Method 1: 仅环境变量
print("\n--- Method 1: 仅环境变量 ---")
try:
    llm1 = ChatBot(llm_provider="gemini", model_name="gemini-2.5-pro")
    print("✅ ChatBot created")
    print(f"   Type: {type(llm1)}")
    print(f"   Has _api_key: {hasattr(llm1, '_api_key')}")
    print(f"   Has api_key: {hasattr(llm1, 'api_key')}")
    print(f"   Has config: {hasattr(llm1, 'config')}")
    
    if hasattr(llm1, '_api_key'):
        val = getattr(llm1, '_api_key', None)
        print(f"   _api_key value: {val[:30] if val else 'None'}...")
    if hasattr(llm1, 'api_key'):
        val = getattr(llm1, 'api_key', None)
        print(f"   api_key value: {val[:30] if val else 'None'}...")
    if hasattr(llm1, 'config'):
        print(f"   config value: {getattr(llm1, 'config', None)}")
    
    # 尝试调用
    print("\n   Testing chat()...")
    try:
        response = asyncio.run(llm1.chat("Say 'OK'"))
        print(f"   ✅ SUCCESS: {response}")
        test_results['method1'] = 'SUCCESS'
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        test_results['method1'] = str(e)
        
except Exception as e:
    print(f"❌ Failed to create ChatBot: {e}")
    test_results['method1'] = f"Init failed: {e}"

# Method 2: 传递 api_key 参数
print("\n--- Method 2: 传递 api_key 参数 ---")
try:
    llm2 = ChatBot(llm_provider="gemini", model_name="gemini-2.5-pro", api_key=Config.GEMINI_API_KEY)
    print("✅ ChatBot created with api_key parameter")
    
    if hasattr(llm2, '_api_key'):
        val = getattr(llm2, '_api_key', None)
        print(f"   _api_key value: {val[:30] if val else 'None'}...")
    if hasattr(llm2, 'api_key'):
        val = getattr(llm2, 'api_key', None)
        print(f"   api_key value: {val[:30] if val else 'None'}...")
    
    print("\n   Testing chat()...")
    try:
        response = asyncio.run(llm2.chat("Say 'OK'"))
        print(f"   ✅ SUCCESS: {response}")
        test_results['method2'] = 'SUCCESS'
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        test_results['method2'] = str(e)
        
except TypeError as e:
    print(f"⚠️  ChatBot doesn't accept api_key parameter: {e}")
    test_results['method2'] = f"Not supported: {e}"
except Exception as e:
    print(f"❌ Failed: {e}")
    test_results['method2'] = f"Init failed: {e}"

# Method 3: 使用 **kwargs
print("\n--- Method 3: 使用 **kwargs ---")
try:
    kwargs = {
        'llm_provider': 'gemini',
        'model_name': 'gemini-2.5-pro',
        'gemini_api_key': Config.GEMINI_API_KEY
    }
    llm3 = ChatBot(**kwargs)
    print("✅ ChatBot created with gemini_api_key in kwargs")
    
    print("\n   Testing chat()...")
    try:
        response = asyncio.run(llm3.chat("Say 'OK'"))
        print(f"   ✅ SUCCESS: {response}")
        test_results['method3'] = 'SUCCESS'
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        test_results['method3'] = str(e)
        
except Exception as e:
    print(f"❌ Failed: {e}")
    test_results['method3'] = f"Init failed: {e}"

# Step 6: 检查 SpoonAI 内部如何读取 API key
print("\n[Step 6] 检查 ChatBot 内部属性")
try:
    llm_test = ChatBot(llm_provider="gemini", model_name="gemini-2.5-pro")
    
    print("\n所有属性:")
    for attr in dir(llm_test):
        if not attr.startswith('_'):
            try:
                val = getattr(llm_test, attr)
                if not callable(val):
                    print(f"  {attr}: {val}")
            except:
                pass
    
    print("\n私有属性 (可能包含API key):")
    for attr in dir(llm_test):
        if attr.startswith('_') and 'key' in attr.lower():
            try:
                val = getattr(llm_test, attr)
                if isinstance(val, str) and len(val) > 0:
                    print(f"  {attr}: {val[:30]}...")
            except:
                pass
                
except Exception as e:
    print(f"❌ Failed to inspect: {e}")

# Step 7: 测试 SpoonReactAI
print("\n[Step 7] 测试 SpoonReactAI wrapper")
try:
    from spoon_ai.agents import SpoonReactAI
    
    llm_base = ChatBot(llm_provider="gemini", model_name="gemini-2.5-pro", api_key=Config.GEMINI_API_KEY)
    agent = SpoonReactAI(llm=llm_base)
    print("✅ SpoonReactAI created")
    
    print("\n   Testing agent.run()...")
    try:
        response = asyncio.run(agent.run("Say 'OK'"))
        print(f"   ✅ SUCCESS: {response}")
        test_results['spoon_react'] = 'SUCCESS'
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        test_results['spoon_react'] = str(e)
        
        # 打印详细错误
        print("\n   详细错误追踪:")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"❌ Failed: {e}")
    test_results['spoon_react'] = f"Init failed: {e}"
    import traceback
    traceback.print_exc()

# 总结
print("\n" + "="*80)
print("测试结果总结")
print("="*80)
for method, result in test_results.items():
    status = "✅" if result == 'SUCCESS' else "❌"
    print(f"{status} {method}: {result}")

print("\n" + "="*80)
print("诊断建议")
print("="*80)

if all(r == 'SUCCESS' for r in test_results.values()):
    print("✅ 所有测试通过！API key配置正确。")
elif 'SUCCESS' in test_results.values():
    success_methods = [k for k, v in test_results.items() if v == 'SUCCESS']
    print(f"✅ 部分方法成功: {success_methods}")
    print(f"建议: 使用成功的初始化方法")
else:
    print("❌ 所有方法都失败了！")
    
    # 分析错误模式
    auth_errors = [k for k, v in test_results.items() if 'Authentication failed' in v or 'API key' in v]
    if auth_errors:
        print("\n🔍 认证错误分析:")
        print("   问题: SpoonAI 内部无法访问 API key")
        print("\n   可能原因:")
        print("   1. SpoonAI 使用了不同的环境变量名")
        print("   2. SpoonAI 期望不同的初始化参数")
        print("   3. SpoonAI 底层调用了 Google SDK，但没有正确传递 API key")
        print("\n   解决方案:")
        print("   a) 检查 SpoonAI 源码: spoon_ai/chat.py 和 spoon_ai/providers/gemini.py")
        print("   b) 尝试设置: GOOGLE_API_KEY, GENAI_API_KEY")
        print("   c) 考虑直接使用 Google Generative AI SDK 而不是 SpoonAI")

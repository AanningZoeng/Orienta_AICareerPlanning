"""诊断环境变量来源"""
import os
import sys
from pathlib import Path

print("="*70)
print("环境变量诊断工具")
print("="*70)

# 1. 检查系统环境变量（在load_dotenv之前）
print("\n【1】运行脚本前的系统环境变量:")
print(f"  GEMINI_API_KEY = {os.environ.get('GEMINI_API_KEY', 'NOT SET')}")

# 2. 查找所有可能的 .env 文件
print("\n【2】查找项目中的 .env 文件:")
project_root = Path(__file__).parent.parent
for env_file in project_root.rglob('.env'):
    print(f"  找到: {env_file}")
    print(f"    存在: {env_file.exists()}")
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                if 'GEMINI_API_KEY' in line and not line.strip().startswith('#'):
                    print(f"    内容: {line.strip()}")

# 3. 检查 config.py 会加载哪个 .env
print("\n【3】config.py 的 .env 路径:")
sys.path.insert(0, str(project_root))
from backend.config import Config

config_root = Path(__file__).parent.parent / 'backend' / 'config.py'
config_file = Path(__file__).parent.parent / 'backend' / 'config.py'
print(f"  config.py 位置: {config_file}")

# 从 config.py 计算 .env 路径
from backend.config import ROOT_DIR, env_path
print(f"  ROOT_DIR = {ROOT_DIR}")
print(f"  env_path = {env_path}")
print(f"  存在: {env_path.exists()}")

# 4. 读取 .env 文件内容
if env_path.exists():
    print(f"\n【4】.env 文件实际内容:")
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
        for line in content.split('\n'):
            if 'GEMINI_API_KEY' in line:
                print(f"  {line}")

# 5. 检查 Config 类读取的值
print(f"\n【5】Config 类读取的值:")
print(f"  Config.GEMINI_API_KEY = {Config.GEMINI_API_KEY}")
print(f"  前30字符: {Config.GEMINI_API_KEY[:30] if Config.GEMINI_API_KEY else 'EMPTY'}...")

# 6. 检查 os.environ（load_dotenv之后）
print(f"\n【6】load_dotenv 后的 os.environ:")
print(f"  os.environ['GEMINI_API_KEY'] = {os.environ.get('GEMINI_API_KEY', 'NOT SET')}")

# 7. 对比
print(f"\n【7】对比分析:")
env_before = "AIzaSyB2ZLJc0vcR2EYOlQd6-HAsUuB2A1TFido"  # 你看到的错误值
env_file = "AIzaSyBa2c_QPxNjnmfVMLNTFGrX8D185gB0Ezs"  # .env 文件中的正确值

current = Config.GEMINI_API_KEY
if current == env_before:
    print(f"  ❌ 当前值匹配系统环境变量（错误的旧key）")
    print(f"  问题：系统环境变量覆盖了 .env 文件")
    print(f"  解决方案：清除系统环境变量中的 GEMINI_API_KEY")
elif current == env_file:
    print(f"  ✅ 当前值匹配 .env 文件（正确）")
else:
    print(f"  ⚠️  当前值不匹配任何已知来源")
    print(f"    当前值: {current[:30]}...")

print("\n" + "="*70)
print("诊断建议:")
print("="*70)
print("如果系统环境变量覆盖了 .env 文件，请运行:")
print("  PowerShell: $env:GEMINI_API_KEY = $null")
print("  或者删除系统环境变量后重启终端")

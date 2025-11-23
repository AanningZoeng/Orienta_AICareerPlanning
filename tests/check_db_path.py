"""检查数据库路径配置"""
import sys
import os
from pathlib import Path
import warnings

# Suppress deprecation warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.config import Config
from backend.agents.career_analysis_agent import create_career_analysis_agent

print("\n" + "="*60)
print("数据库路径配置检查")
print("="*60)

# Check agent's db path
print("\n正在创建 CareerAnalysisAgent...")
agent = create_career_analysis_agent()

print(f"\n✓ CareerAnalysisAgent 数据库路径:")
print(f"  {agent.db_path}")

print(f"\n✓ 绝对路径:")
print(f"  {agent.db_path.resolve()}")

print(f"\n✓ 文件存在: {agent.db_path.exists()}")

if agent.db_path.exists():
    import sqlite3
    try:
        conn = sqlite3.connect(agent.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM jobs')
        count = cursor.fetchone()[0]
        print(f"✓ 数据库记录数: {count} 条职位")
        conn.close()
        
        print(f"\n✅ 数据库配置正确且可用！")
    except Exception as e:
        print(f"✗ 数据库查询失败: {e}")
else:
    print(f"\n⚠️  数据库文件不存在")
    print(f"\n创建数据库:")
    print(f"  python tests\\create_sample_db.py")

print(f"\n期望位置: backend\\agents\\job_info.db")
print("="*60 + "\n")

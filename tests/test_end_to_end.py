"""End-to-end test: Major Research → Career Analysis with Database Integration"""
import asyncio
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.config import Config
from backend.agents.major_research_agent import create_major_research_agent
from backend.agents.career_analysis_agent import create_career_analysis_agent


async def main():
    print("\n" + "="*80)
    print("端到端测试: Major → Career → Database Integration")
    print("="*80)
    
    # Step 0: Check if database exists
    print("\n[准备] 检查数据库")
    print("-"*80)
    career_agent = create_career_analysis_agent()
    
    if not career_agent.db_path.exists():
        print(f"⚠️  数据库未找到: {career_agent.db_path}")
        print(f"\n请先运行: python tests\\create_sample_db.py")
        print(f"然后重新运行此测试\n")
        return
    
    print(f"✅ 数据库存在: {career_agent.db_path}")
    
    # Check scikit-learn
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        print(f"✅ scikit-learn 已安装")
    except ImportError:
        print(f"⚠️  scikit-learn 未安装 - 数据库功能将被禁用")
        print(f"   安装命令: pip install scikit-learn")
    
    # Step 1: Generate majors
    print("\n[步骤 1] 生成专业分析")
    print("-"*80)
    
    major_agent = create_major_research_agent()
    test_query = "我对技术和数据分析感兴趣，想找一个有良好就业前景的专业"
    
    print(f"用户查询: {test_query}")
    print(f"正在生成专业建议...")
    
    major_results = await major_agent.process_query(test_query)
    
    print(f"\n✅ 生成了 {len(major_results)} 个专业:")
    for major_name in major_results.keys():
        print(f"   - {major_name}")
    
    # Check saved JSON
    db_dir = Path(__file__).parent.parent / "backend" / "database"
    major_json = db_dir / "majors_latest.json"
    
    if major_json.exists():
        print(f"\n✅ 专业数据已保存: majors_latest.json")
    else:
        print(f"\n❌ 未找到 majors_latest.json")
        return
    
    # Step 2: Generate career analysis with database
    print("\n[步骤 2] 生成职业分析 (集成数据库)")
    print("-"*80)
    
    print(f"读取专业数据并分析职业...")
    career_results = await career_agent.process_query()
    
    print(f"\n✅ 处理完成!")
    
    # Step 3: Display results
    print("\n[步骤 3] 输出结果验证")
    print("-"*80)
    
    total_careers = 0
    total_db_matches = 0
    
    for major_name, careers in career_results.items():
        print(f"\n📚 专业: {major_name}")
        print(f"   职业数量: {len(careers)}")
        
        for career_title, career_data in careers.items():
            total_careers += 1
            db_matches = career_data.get('db_match_count', 0)
            total_db_matches += db_matches
            
            print(f"\n   💼 {career_title}")
            print(f"      └─ 描述: {len(career_data.get('description', ''))} 字符")
            print(f"      └─ 资源: {len(career_data.get('resources', []))} URLs")
            
            salary = career_data.get('salary', {})
            salary_min = salary.get('min', 0)
            salary_max = salary.get('max', 0)
            
            if salary_min > 0 or salary_max > 0:
                print(f"      └─ 薪资: ${salary_min:,.0f} - ${salary_max:,.0f} {salary.get('currency', 'USD')}")
            else:
                print(f"      └─ 薪资: 无数据库匹配")
            
            print(f"      └─ 职位示例: {len(career_data.get('job_examples', []))} 条")
            print(f"      └─ DB匹配: {db_matches} 个职位")
            
            # Show one example if available
            examples = career_data.get('job_examples', [])
            if examples:
                ex = examples[0]
                print(f"         示例: {ex.get('job_title')} @ {ex.get('company')}")
                print(f"                {ex.get('salary_range')}")
    
    # Step 4: Verify saved JSON structure
    print("\n[步骤 4] 验证保存的JSON结构")
    print("-"*80)
    
    career_json = db_dir / "careers_latest.json"
    
    if career_json.exists():
        with open(career_json, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        print(f"✅ JSON文件已保存: careers_latest.json")
        print(f"\n文件结构:")
        print(f"   ├─ timestamp: {saved_data.get('timestamp')}")
        print(f"   ├─ user_query: {saved_data.get('user_query')}")
        print(f"   └─ careers: {len(saved_data.get('careers', {}))} 个专业")
        
        # Verify structure matches requirement
        print(f"\n结构验证:")
        careers_data = saved_data.get('careers', {})
        
        if careers_data:
            sample_major = list(careers_data.keys())[0]
            sample_career_name = list(careers_data[sample_major].keys())[0]
            sample_career = careers_data[sample_major][sample_career_name]
            
            required_fields = ['description', 'resources', 'salary', 'job_examples', 'db_match_count']
            missing_fields = [f for f in required_fields if f not in sample_career]
            
            if missing_fields:
                print(f"   ❌ 缺少字段: {missing_fields}")
            else:
                print(f"   ✅ 所有必需字段存在")
                print(f"      ├─ description: str ({len(sample_career['description'])} chars)")
                print(f"      ├─ resources: list ({len(sample_career['resources'])} URLs)")
                print(f"      ├─ salary: dict (min={sample_career['salary'].get('min')}, max={sample_career['salary'].get('max')})")
                print(f"      ├─ job_examples: list ({len(sample_career['job_examples'])} items)")
                print(f"      └─ db_match_count: int ({sample_career['db_match_count']})")
    else:
        print(f"❌ 未找到 careers_latest.json")
    
    # Final summary
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    
    print(f"\n📊 统计:")
    print(f"   专业数量: {len(career_results)}")
    print(f"   职业总数: {total_careers}")
    print(f"   数据库匹配总数: {total_db_matches}")
    
    if total_db_matches > 0:
        avg_matches = total_db_matches / total_careers if total_careers > 0 else 0
        print(f"   平均匹配数: {avg_matches:.1f} 个/职业")
    
    print(f"\n✅ 端到端测试完成!")
    print(f"\n💾 生成的文件:")
    print(f"   1. backend/database/majors_latest.json")
    print(f"   2. backend/database/careers_latest.json")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

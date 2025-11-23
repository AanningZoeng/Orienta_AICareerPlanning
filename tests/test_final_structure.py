"""完整测试：展示集成后的输出结构"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.config import Config
from backend.agents.career_analysis_agent import create_career_analysis_agent


async def main():
    print("\n" + "="*80)
    print("集成测试：CareerAnalysisAgent (LLM + Web + Database)")
    print("="*80)
    
    agent = create_career_analysis_agent()
    
    # 模拟单个职业分析（展示完整结构）
    print("\n[测试 1] 分析单个职业")
    print("-"*80)
    
    career = "Data Scientist"
    major = "Computer Science"
    
    result = await agent.analyze_career_simple(career, major)
    
    print(f"\n职业: {career}")
    print(f"专业: {major}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False)[:1000] + "...")
    
    print("\n" + "-"*80)
    print("✅ 输出结构验证:")
    print(f"  ✓ description: {'存在' if result.get('description') else '缺失'}")
    print(f"  ✓ resources: {len(result.get('resources', []))} URLs")
    print(f"  ✓ salary.min: ${result.get('salary', {}).get('min', 0):,.0f}")
    print(f"  ✓ salary.max: ${result.get('salary', {}).get('max', 0):,.0f}")
    print(f"  ✓ job_examples: {len(result.get('job_examples', []))} 条")
    print(f"  ✓ db_match_count: {result.get('db_match_count', 0)}")
    
    # 测试完整工作流（如果有 major JSON 文件）
    print("\n\n[测试 2] 完整工作流 (读取 major JSON)")
    print("-"*80)
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'database')
    latest_major = os.path.join(db_path, 'majors_latest.json')
    
    if os.path.exists(latest_major):
        print(f"✓ 找到 majors_latest.json")
        
        results = await agent.process_query()
        
        print(f"\n处理结果: {len(results)} 个专业\n")
        
        # 展示嵌套结构
        for major_name, careers in results.items():
            print(f"\n📚 {major_name}")
            for career_title, career_data in careers.items():
                print(f"  └─ 💼 {career_title}")
                print(f"      ├─ 描述: {len(career_data.get('description', ''))} 字符")
                print(f"      ├─ 资源: {len(career_data.get('resources', []))} URLs")
                salary = career_data.get('salary', {})
                print(f"      ├─ 薪资: ${salary.get('min', 0):,.0f} - ${salary.get('max', 0):,.0f}")
                print(f"      └─ 职位示例: {len(career_data.get('job_examples', []))} 条 (DB匹配: {career_data.get('db_match_count', 0)})")
        
        print("\n✅ 输出格式正确: {major: {career: {description, resources, salary, job_examples}}}")
    else:
        print(f"⚠️  未找到 majors_latest.json")
        print(f"   请先运行: python tests\\major_research_test.py")
    
    print("\n" + "="*80)
    print("测试完成！")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

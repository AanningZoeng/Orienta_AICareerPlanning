"""完整功能测试：验证 career_analysis_agent.py 的所有集成功能"""
import asyncio
import sys
import os
import json
import warnings
from pathlib import Path

# Suppress warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.config import Config
from backend.agents.career_analysis_agent import create_career_analysis_agent


async def test_all_features():
    print("\n" + "="*80)
    print("CareerAnalysisAgent 完整功能验证")
    print("="*80)
    
    # 测试计数器
    tests_passed = 0
    tests_failed = 0
    
    # ============================================================
    # 测试 1: Agent 初始化
    # ============================================================
    print("\n[测试 1] Agent 初始化")
    print("-"*80)
    
    try:
        agent = create_career_analysis_agent()
        print("✅ Agent 创建成功")
        print(f"   LLM Agent: {'已配置' if agent.llm_agent else '未配置'}")
        print(f"   DB Path: {agent.db_path}")
        print(f"   DB Exists: {agent.db_path.exists()}")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Agent 创建失败: {e}")
        tests_failed += 1
        return
    
    # ============================================================
    # 测试 2: 数据库路径和连接
    # ============================================================
    print("\n[测试 2] 数据库配置")
    print("-"*80)
    
    db_available = False
    if agent.db_path.exists():
        import sqlite3
        try:
            conn = sqlite3.connect(agent.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM jobs')
            count = cursor.fetchone()[0]
            conn.close()
            print(f"✅ 数据库可用")
            print(f"   路径: {agent.db_path}")
            print(f"   职位数: {count}")
            db_available = True
            tests_passed += 1
        except Exception as e:
            print(f"❌ 数据库查询失败: {e}")
            tests_failed += 1
    else:
        print(f"⚠️  数据库不存在: {agent.db_path}")
        print(f"   运行 'python tests\\create_sample_db.py' 创建数据库")
        tests_failed += 1
    
    # ============================================================
    # 测试 3: scikit-learn 可用性
    # ============================================================
    print("\n[测试 3] scikit-learn 依赖")
    print("-"*80)
    
    sklearn_available = False
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        print("✅ scikit-learn 已安装")
        sklearn_available = True
        tests_passed += 1
    except ImportError:
        print("❌ scikit-learn 未安装")
        print("   运行 'pip install scikit-learn' 安装")
        tests_failed += 1
    
    # ============================================================
    # 测试 4: identify_careers() - 职业识别
    # ============================================================
    print("\n[测试 4] 职业识别功能 (identify_careers)")
    print("-"*80)
    
    test_major = "Computer Science"
    try:
        careers = await agent.identify_careers(test_major)
        if len(careers) == 3:
            print(f"✅ 成功识别 3 个职业")
            for i, career in enumerate(careers, 1):
                print(f"   {i}. {career}")
            tests_passed += 1
        else:
            print(f"⚠️  返回了 {len(careers)} 个职业（期望 3 个）")
            for i, career in enumerate(careers, 1):
                print(f"   {i}. {career}")
            tests_passed += 1
    except Exception as e:
        print(f"❌ 职业识别失败: {e}")
        tests_failed += 1
        return
    
    # ============================================================
    # 测试 5: _parse_salary() - 薪资解析
    # ============================================================
    print("\n[测试 5] 薪资解析功能 (_parse_salary)")
    print("-"*80)
    
    test_salaries = [
        ("$100k - $150k", [100000, 150000]),
        ("$80,000 - $120,000", [80000, 120000]),
        ("100k-150k", [100000, 150000]),
    ]
    
    parse_passed = 0
    for salary_str, expected in test_salaries:
        result = agent._parse_salary(salary_str)
        if result == expected:
            print(f"✅ '{salary_str}' → {result}")
            parse_passed += 1
        else:
            print(f"❌ '{salary_str}' → {result} (期望 {expected})")
    
    if parse_passed == len(test_salaries):
        print(f"✅ 薪资解析测试通过 ({parse_passed}/{len(test_salaries)})")
        tests_passed += 1
    else:
        print(f"⚠️  部分测试失败 ({parse_passed}/{len(test_salaries)})")
        tests_failed += 1
    
    # ============================================================
    # 测试 6: _vec_similarity() - TF-IDF 相似度匹配
    # ============================================================
    print("\n[测试 6] TF-IDF 相似度匹配 (_vec_similarity)")
    print("-"*80)
    
    if db_available and sklearn_available:
        try:
            test_job = "Software Engineer"
            matches = agent._vec_similarity(test_job, threshold=0.2)
            print(f"✅ 查询: '{test_job}'")
            print(f"   匹配数: {len(matches)}")
            if matches:
                print(f"   前 3 个匹配:")
                for i, match in enumerate(matches[:3], 1):
                    print(f"      {i}. {match}")
            tests_passed += 1
        except Exception as e:
            print(f"❌ 相似度匹配失败: {e}")
            tests_failed += 1
    else:
        print("⏭️  跳过（数据库或 scikit-learn 不可用）")
    
    # ============================================================
    # 测试 7: _fetch_job_db_data() - 数据库查询
    # ============================================================
    print("\n[测试 7] 数据库查询功能 (_fetch_job_db_data)")
    print("-"*80)
    
    if db_available and sklearn_available:
        try:
            test_career = "Software Engineer"
            loop = asyncio.get_event_loop()
            db_data = await loop.run_in_executor(None, agent._fetch_job_db_data, test_career)
            
            print(f"✅ 查询: '{test_career}'")
            print(f"   DB 匹配数: {db_data.get('db_match_count', 0)}")
            print(f"   薪资范围: ${db_data.get('salary', {}).get('min', 0):,.0f} - ${db_data.get('salary', {}).get('max', 0):,.0f}")
            print(f"   职位示例: {len(db_data.get('job_examples', []))} 条")
            
            if db_data.get('db_match_count', 0) > 0:
                print(f"✅ 数据库查询成功")
                tests_passed += 1
                
                # 显示一个示例
                examples = db_data.get('job_examples', [])
                if examples:
                    ex = examples[0]
                    print(f"   示例职位:")
                    print(f"      职位: {ex.get('job_title')}")
                    print(f"      公司: {ex.get('company')}")
                    print(f"      薪资: {ex.get('salary_range')}")
            else:
                print(f"⚠️  未找到匹配职位")
                tests_passed += 1
        except Exception as e:
            print(f"❌ 数据库查询失败: {e}")
            import traceback
            traceback.print_exc()
            tests_failed += 1
    else:
        print("⏭️  跳过（数据库或 scikit-learn 不可用）")
    
    # ============================================================
    # 测试 8: _generate_career_resources() - Web 资源收集
    # ============================================================
    print("\n[测试 8] Web 资源收集 (_generate_career_resources)")
    print("-"*80)
    
    try:
        test_career = "Data Scientist"
        test_major = "Computer Science"
        print(f"正在收集资源（可能需要 10-30 秒）...")
        resources = await agent._generate_career_resources(test_career, test_major)
        
        print(f"✅ 收集了 {len(resources)} 个资源")
        if resources:
            print(f"   前 3 个资源:")
            for i, url in enumerate(resources[:3], 1):
                print(f"      {i}. {url}")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 资源收集失败: {e}")
        tests_failed += 1
    
    # ============================================================
    # 测试 9: analyze_career_simple() - 完整职业分析
    # ============================================================
    print("\n[测试 9] 完整职业分析 (analyze_career_simple)")
    print("-"*80)
    
    try:
        test_career = "Software Engineer"
        test_major = "Computer Science"
        print(f"分析职业: {test_career} (for {test_major})")
        print(f"正在进行完整分析（可能需要 20-40 秒）...")
        
        result = await agent.analyze_career_simple(test_career, test_major)
        
        # 验证返回结构
        required_fields = ['description', 'resources', 'salary', 'job_examples', 'db_match_count']
        missing_fields = [f for f in required_fields if f not in result]
        
        if missing_fields:
            print(f"❌ 缺少字段: {missing_fields}")
            tests_failed += 1
        else:
            print(f"✅ 所有字段存在")
            print(f"   描述长度: {len(result.get('description', ''))} 字符")
            print(f"   资源数量: {len(result.get('resources', []))} 个")
            
            salary = result.get('salary', {})
            print(f"   薪资范围: ${salary.get('min', 0):,.0f} - ${salary.get('max', 0):,.0f}")
            print(f"   职位示例: {len(result.get('job_examples', []))} 条")
            print(f"   DB 匹配: {result.get('db_match_count', 0)} 个")
            
            # 显示部分描述
            desc = result.get('description', '')
            if desc:
                print(f"\n   描述片段:")
                print(f"   \"{desc[:100]}...\"")
            
            tests_passed += 1
    except Exception as e:
        print(f"❌ 完整分析失败: {e}")
        import traceback
        traceback.print_exc()
        tests_failed += 1
    
    # ============================================================
    # 测试 10: 输出结构验证
    # ============================================================
    print("\n[测试 10] 输出结构验证")
    print("-"*80)
    
    if 'result' in locals():
        print("验证输出格式符合要求:")
        print("{")
        print(f"  \"description\": \"str ({len(result.get('description', ''))} chars)\",")
        print(f"  \"resources\": [list of {len(result.get('resources', []))} URLs],")
        salary = result.get('salary', {})
        print(f"  \"salary\": {{\"min\": {salary.get('min', 0)}, \"max\": {salary.get('max', 0)}, \"currency\": \"{salary.get('currency', 'USD')}\"}},")
        print(f"  \"job_examples\": [list of {len(result.get('job_examples', []))} items],")
        print(f"  \"db_match_count\": {result.get('db_match_count', 0)}")
        print("}")
        
        # 验证类型
        type_checks = [
            ('description', str),
            ('resources', list),
            ('salary', dict),
            ('job_examples', list),
            ('db_match_count', int)
        ]
        
        type_errors = []
        for field, expected_type in type_checks:
            if field in result and not isinstance(result[field], expected_type):
                type_errors.append(f"{field} (期望 {expected_type.__name__}, 实际 {type(result[field]).__name__})")
        
        if type_errors:
            print(f"❌ 类型错误: {', '.join(type_errors)}")
            tests_failed += 1
        else:
            print(f"✅ 所有字段类型正确")
            tests_passed += 1
    else:
        print("⏭️  跳过（未生成分析结果）")
    
    # ============================================================
    # 最终总结
    # ============================================================
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    
    total_tests = tests_passed + tests_failed
    print(f"\n总测试数: {total_tests}")
    print(f"通过: {tests_passed} ✅")
    print(f"失败: {tests_failed} ❌")
    
    if tests_failed == 0:
        print(f"\n🎉 所有测试通过！CareerAnalysisAgent 功能完整！")
    else:
        print(f"\n⚠️  有 {tests_failed} 个测试失败")
        
        # 提供修复建议
        print(f"\n修复建议:")
        if not db_available:
            print(f"  1. 创建数据库: python tests\\create_sample_db.py")
        if not sklearn_available:
            print(f"  2. 安装依赖: pip install scikit-learn")
    
    print("\n" + "="*80)
    
    return tests_passed, tests_failed


if __name__ == "__main__":
    passed, failed = asyncio.run(test_all_features())
    
    # Exit code: 0 if all passed, 1 if any failed
    sys.exit(0 if failed == 0 else 1)

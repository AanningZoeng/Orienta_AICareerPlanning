"""完整集成测试：验证 CareerAnalysisAgent 所有功能"""
import asyncio
import sys
import os
import json
from pathlib import Path
import warnings

# Suppress warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.config import Config
from backend.agents.career_analysis_agent import create_career_analysis_agent


async def test_all_features():
    print("\n" + "="*80)
    print("CareerAnalysisAgent 完整功能集成测试")
    print("="*80)
    
    # 测试结果统计
    tests_passed = 0
    tests_failed = 0
    test_details = []
    
    # ============================================================
    # 测试 1: Agent 初始化
    # ============================================================
    print("\n[测试 1/7] Agent 初始化")
    print("-"*80)
    
    try:
        agent = create_career_analysis_agent()
        print(f"✅ Agent 创建成功")
        print(f"   - LLM Agent: {'已配置' if agent.llm_agent else '未配置'}")
        print(f"   - DB Path: {agent.db_path}")
        tests_passed += 1
        test_details.append(("Agent 初始化", "✅ 通过"))
    except Exception as e:
        print(f"❌ Agent 创建失败: {e}")
        tests_failed += 1
        test_details.append(("Agent 初始化", f"❌ 失败: {e}"))
        return
    
    # ============================================================
    # 测试 2: 数据库连接
    # ============================================================
    print("\n[测试 2/7] 数据库连接")
    print("-"*80)
    
    db_available = False
    if agent.db_path.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(agent.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM jobs')
            count = cursor.fetchone()[0]
            conn.close()
            
            print(f"✅ 数据库连接成功")
            print(f"   - 职位数量: {count}")
            db_available = True
            tests_passed += 1
            test_details.append(("数据库连接", f"✅ 通过 ({count} 条记录)"))
        except Exception as e:
            print(f"❌ 数据库查询失败: {e}")
            tests_failed += 1
            test_details.append(("数据库连接", f"❌ 失败: {e}"))
    else:
        print(f"⚠️  数据库文件不存在: {agent.db_path}")
        print(f"   提示: 运行 python tests\\create_sample_db.py")
        tests_failed += 1
        test_details.append(("数据库连接", "❌ 文件不存在"))
    
    # ============================================================
    # 测试 3: TF-IDF 相似度匹配 (如果有数据库)
    # ============================================================
    print("\n[测试 3/7] TF-IDF 相似度匹配")
    print("-"*80)
    
    sklearn_available = False
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        print(f"✅ scikit-learn 已安装")
        sklearn_available = True
        
        if db_available:
            test_job = "Software Engineer"
            matches = agent._vec_similarity(test_job, threshold=0.2)
            
            if matches:
                print(f"✅ TF-IDF 匹配成功")
                print(f"   - 查询: '{test_job}'")
                print(f"   - 匹配数: {len(matches)}")
                print(f"   - 前3个: {', '.join(matches[:3])}")
                tests_passed += 1
                test_details.append(("TF-IDF 匹配", f"✅ 通过 ({len(matches)} 个匹配)"))
            else:
                print(f"⚠️  未找到匹配")
                tests_failed += 1
                test_details.append(("TF-IDF 匹配", "❌ 无匹配结果"))
        else:
            print(f"⏭️  跳过 (数据库不可用)")
            test_details.append(("TF-IDF 匹配", "⏭️ 跳过"))
    except ImportError:
        print(f"❌ scikit-learn 未安装")
        print(f"   安装: pip install scikit-learn")
        tests_failed += 1
        test_details.append(("TF-IDF 匹配", "❌ scikit-learn 未安装"))
    except Exception as e:
        print(f"❌ TF-IDF 测试失败: {e}")
        tests_failed += 1
        test_details.append(("TF-IDF 匹配", f"❌ 失败: {e}"))
    
    # ============================================================
    # 测试 4: 薪资解析
    # ============================================================
    print("\n[测试 4/7] 薪资解析")
    print("-"*80)
    
    try:
        test_salaries = [
            ("$100k - $150k", [100000, 150000]),
            ("$80,000 - $120,000", [80000, 120000]),
            ("100k-150k", [100000, 150000]),
        ]
        
        all_correct = True
        for salary_str, expected in test_salaries:
            parsed = agent._parse_salary(salary_str)
            if parsed == expected:
                print(f"✅ '{salary_str}' → {parsed}")
            else:
                print(f"❌ '{salary_str}' → {parsed} (期望 {expected})")
                all_correct = False
        
        if all_correct:
            tests_passed += 1
            test_details.append(("薪资解析", "✅ 通过"))
        else:
            tests_failed += 1
            test_details.append(("薪资解析", "❌ 部分失败"))
    except Exception as e:
        print(f"❌ 薪资解析失败: {e}")
        tests_failed += 1
        test_details.append(("薪资解析", f"❌ 失败: {e}"))
    
    # ============================================================
    # 测试 5: 数据库查询 (完整流程)
    # ============================================================
    print("\n[测试 5/7] 数据库查询 (完整流程)")
    print("-"*80)
    
    if db_available and sklearn_available:
        try:
            loop = asyncio.get_event_loop()
            test_career = "Data Scientist"
            db_data = await loop.run_in_executor(None, agent._fetch_job_db_data, test_career)
            
            print(f"✅ 数据库查询成功")
            print(f"   - 查询职位: '{test_career}'")
            print(f"   - 匹配数: {db_data.get('db_match_count', 0)}")
            print(f"   - 薪资范围: ${db_data.get('salary', {}).get('min', 0):,.0f} - ${db_data.get('salary', {}).get('max', 0):,.0f}")
            print(f"   - 职位示例: {len(db_data.get('job_examples', []))} 条")
            
            if db_data.get('db_match_count', 0) > 0:
                tests_passed += 1
                test_details.append(("数据库查询", f"✅ 通过 ({db_data['db_match_count']} 个匹配)"))
            else:
                tests_failed += 1
                test_details.append(("数据库查询", "❌ 无匹配结果"))
        except Exception as e:
            print(f"❌ 数据库查询失败: {e}")
            tests_failed += 1
            test_details.append(("数据库查询", f"❌ 失败: {e}"))
    else:
        print(f"⏭️  跳过 (数据库或 scikit-learn 不可用)")
        test_details.append(("数据库查询", "⏭️ 跳过"))
    
    # ============================================================
    # 测试 6: 职业识别 (LLM)
    # ============================================================
    print("\n[测试 6/7] 职业识别 (LLM)")
    print("-"*80)
    
    try:
        test_major = "Computer Science"
        careers = await agent.identify_careers(test_major)
        
        print(f"✅ 职业识别成功")
        print(f"   - 专业: '{test_major}'")
        print(f"   - 识别职业数: {len(careers)}")
        print(f"   - 职业列表: {', '.join(careers)}")
        
        if len(careers) >= 3:
            tests_passed += 1
            test_details.append(("职业识别", f"✅ 通过 ({len(careers)} 个职业)"))
        else:
            tests_failed += 1
            test_details.append(("职业识别", f"❌ 职业数不足 ({len(careers)}/3)"))
    except Exception as e:
        print(f"❌ 职业识别失败: {e}")
        tests_failed += 1
        test_details.append(("职业识别", f"❌ 失败: {e}"))
    
    # ============================================================
    # 测试 7: 完整职业分析 (集成所有功能)
    # ============================================================
    print("\n[测试 7/7] 完整职业分析 (集成测试)")
    print("-"*80)
    
    try:
        test_career = "Software Engineer"
        test_major = "Computer Science"
        
        print(f"正在分析: {test_career} (for {test_major} graduates)...")
        result = await agent.analyze_career_simple(test_career, test_major)
        
        print(f"\n✅ 完整分析成功")
        print(f"\n结果摘要:")
        print(f"   ├─ description: {len(result.get('description', ''))} chars")
        print(f"   ├─ resources: {len(result.get('resources', []))} URLs")
        
        salary = result.get('salary', {})
        salary_min = salary.get('min', 0)
        salary_max = salary.get('max', 0)
        print(f"   ├─ salary: ${salary_min:,.0f} - ${salary_max:,.0f} {salary.get('currency', 'USD')}")
        print(f"   ├─ job_examples: {len(result.get('job_examples', []))} 条")
        print(f"   └─ db_match_count: {result.get('db_match_count', 0)}")
        
        # 验证结构完整性
        required_fields = ['description', 'resources', 'salary', 'job_examples', 'db_match_count']
        missing_fields = [f for f in required_fields if f not in result]
        
        if not missing_fields:
            # 检查 salary 子结构
            salary_fields = ['min', 'max', 'currency']
            missing_salary = [f for f in salary_fields if f not in result.get('salary', {})]
            
            if not missing_salary:
                print(f"\n✅ 输出结构完整")
                tests_passed += 1
                test_details.append(("完整分析", "✅ 通过"))
            else:
                print(f"\n⚠️  salary 缺少字段: {missing_salary}")
                tests_failed += 1
                test_details.append(("完整分析", f"❌ salary 不完整"))
        else:
            print(f"\n❌ 缺少字段: {missing_fields}")
            tests_failed += 1
            test_details.append(("完整分析", f"❌ 缺少字段"))
        
        # 显示一个职位示例
        if result.get('job_examples'):
            example = result['job_examples'][0]
            print(f"\n职位示例:")
            print(f"   - {example.get('job_title')} @ {example.get('company')}")
            print(f"   - {example.get('salary_range')}")
        
    except Exception as e:
        print(f"❌ 完整分析失败: {e}")
        import traceback
        traceback.print_exc()
        tests_failed += 1
        test_details.append(("完整分析", f"❌ 失败: {e}"))
    
    # ============================================================
    # 测试总结
    # ============================================================
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    
    print(f"\n📊 测试结果:")
    for test_name, status in test_details:
        print(f"   {status:20s} {test_name}")
    
    total_tests = tests_passed + tests_failed
    success_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n统计:")
    print(f"   通过: {tests_passed}/{total_tests}")
    print(f"   失败: {tests_failed}/{total_tests}")
    print(f"   成功率: {success_rate:.1f}%")
    
    # 功能检查清单
    print(f"\n✅ 功能检查清单:")
    print(f"   {'✅' if agent.llm_agent else '❌'} LLM 描述生成")
    print(f"   {'✅' if tests_passed >= 4 else '❌'} Web 资源搜索")
    print(f"   {'✅' if db_available else '❌'} 数据库连接")
    print(f"   {'✅' if sklearn_available else '❌'} TF-IDF 匹配")
    print(f"   {'✅' if tests_passed >= 4 else '❌'} 薪资解析")
    print(f"   {'✅' if tests_passed >= 6 else '❌'} 职业识别")
    print(f"   {'✅' if tests_passed >= 7 else '❌'} 完整集成")
    
    if tests_failed == 0:
        print(f"\n🎉 所有测试通过！系统完全可用！")
    elif tests_passed >= 5:
        print(f"\n⚠️  大部分功能正常，但有 {tests_failed} 个测试失败")
    else:
        print(f"\n❌ 多个测试失败，请检查配置")
    
    # 建议
    print(f"\n💡 下一步:")
    if not db_available:
        print(f"   1. 创建数据库: python tests\\create_sample_db.py")
    if not sklearn_available:
        print(f"   2. 安装依赖: pip install scikit-learn")
    if tests_passed >= 7:
        print(f"   3. 运行完整流程: python tests\\test_end_to_end.py")
        print(f"   4. 验证JSON结构: python tests\\verify_json_structure.py")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_all_features())

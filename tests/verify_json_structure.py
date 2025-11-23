"""Verify the structure of generated JSON files"""
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def verify_json_structure():
    print("\n" + "="*80)
    print("JSON 结构验证工具")
    print("="*80)
    
    db_dir = Path(__file__).parent.parent / "backend" / "database"
    careers_json = db_dir / "careers_latest.json"
    
    if not careers_json.exists():
        print(f"\n❌ 文件未找到: {careers_json}")
        print(f"\n请先运行:")
        print(f"   1. python tests\\major_research_test.py")
        print(f"   2. python tests\\career_analysis_test.py")
        print(f"   或: python tests\\test_end_to_end.py\n")
        return
    
    print(f"\n📄 读取文件: careers_latest.json")
    
    with open(careers_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n✅ JSON 解析成功")
    
    # Top-level structure
    print(f"\n[顶层结构]")
    print(f"  ├─ timestamp: {data.get('timestamp', 'N/A')}")
    print(f"  ├─ source_timestamp: {data.get('source_timestamp', 'N/A')}")
    print(f"  ├─ user_query: {data.get('user_query', 'N/A')[:50]}...")
    print(f"  └─ careers: {len(data.get('careers', {}))} 个专业")
    
    careers = data.get('careers', {})
    
    if not careers:
        print(f"\n⚠️  careers 字段为空")
        return
    
    # Iterate through majors
    print(f"\n[专业 → 职业结构]")
    
    all_valid = True
    total_careers = 0
    total_with_db = 0
    
    required_fields = {
        'description': str,
        'resources': list,
        'salary': dict,
        'job_examples': list,
        'db_match_count': int
    }
    
    for major_name, major_careers in careers.items():
        print(f"\n📚 {major_name}")
        print(f"   职业数量: {len(major_careers)}")
        
        for career_title, career_data in major_careers.items():
            total_careers += 1
            
            print(f"\n   💼 {career_title}")
            
            # Check required fields
            missing_fields = []
            type_errors = []
            
            for field, expected_type in required_fields.items():
                if field not in career_data:
                    missing_fields.append(field)
                    all_valid = False
                else:
                    if not isinstance(career_data[field], expected_type):
                        type_errors.append(f"{field} (期望 {expected_type.__name__}, 实际 {type(career_data[field]).__name__})")
                        all_valid = False
            
            if missing_fields:
                print(f"      ❌ 缺少字段: {', '.join(missing_fields)}")
            
            if type_errors:
                print(f"      ❌ 类型错误: {', '.join(type_errors)}")
            
            if not missing_fields and not type_errors:
                print(f"      ✅ 结构正确")
                
                # Show details
                desc_len = len(career_data.get('description', ''))
                res_count = len(career_data.get('resources', []))
                salary = career_data.get('salary', {})
                examples_count = len(career_data.get('job_examples', []))
                db_matches = career_data.get('db_match_count', 0)
                
                if db_matches > 0:
                    total_with_db += 1
                
                print(f"         ├─ description: {desc_len} chars")
                print(f"         ├─ resources: {res_count} URLs")
                print(f"         ├─ salary: ${salary.get('min', 0):,.0f} - ${salary.get('max', 0):,.0f} {salary.get('currency', 'USD')}")
                print(f"         ├─ job_examples: {examples_count} 条")
                print(f"         └─ db_match_count: {db_matches}")
                
                # Validate salary structure
                if not isinstance(salary, dict):
                    print(f"         ⚠️  salary 不是字典类型")
                    all_valid = False
                else:
                    salary_fields = ['min', 'max', 'currency']
                    missing_salary = [f for f in salary_fields if f not in salary]
                    if missing_salary:
                        print(f"         ⚠️  salary 缺少字段: {', '.join(missing_salary)}")
                        all_valid = False
    
    # Summary
    print(f"\n" + "="*80)
    print(f"验证总结")
    print(f"="*80)
    
    print(f"\n📊 统计:")
    print(f"   专业数量: {len(careers)}")
    print(f"   职业总数: {total_careers}")
    print(f"   有数据库数据的职业: {total_with_db} ({total_with_db/total_careers*100:.1f}%)" if total_careers > 0 else "   有数据库数据的职业: 0")
    
    if all_valid:
        print(f"\n✅ 所有结构验证通过!")
        print(f"\n符合要求的格式:")
        print(f"{{")
        print(f"  \"major\": {{")
        print(f"    \"career\": {{")
        print(f"      \"description\": \"LLM生成\",")
        print(f"      \"resources\": [\"URL列表\"],")
        print(f"      \"salary\": {{\"min\": 80000, \"max\": 150000, \"currency\": \"USD\"}},")
        print(f"      \"job_examples\": [职位示例列表],")
        print(f"      \"db_match_count\": 15")
        print(f"    }}")
        print(f"  }}")
        print(f"}}")
    else:
        print(f"\n❌ 发现结构错误")
    
    print(f"\n" + "="*80 + "\n")


if __name__ == "__main__":
    verify_json_structure()

# CareerAnalysisAgent 集成说明

## 功能概述

集成了两个版本的 CareerAnalysisAgent，实现了完整的职业分析功能：

### Agent 1 功能（Web资源）
- ✅ LLM 生成职业描述
- ✅ DuckDuckGo 搜索在线资源
- ✅ 智能查询生成（LLM提示词）
- ✅ URL 收集和去重

### Agent 2 功能（数据库查询）
- ✅ SQLite 数据库集成
- ✅ TF-IDF 职位匹配
- ✅ 真实薪资数据提取
- ✅ 职位示例展示

## 输出结构

```json
{
  "major_name": {
    "career_title": {
      "description": "LLM生成的职业描述（2-4句话）",
      "resources": [
        "https://example.com/resource1",
        "https://example.com/resource2",
        ...
      ],
      "salary": {
        "min": 80000,
        "max": 150000,
        "currency": "USD"
      },
      "job_examples": [
        {
          "job_title": "Senior Data Scientist",
          "company": "Google",
          "description": "职位描述...",
          "salary_range": "$120k - $180k"
        },
        ...
      ],
      "db_match_count": 15
    }
  }
}
```

## 数据流程

```
用户查询 → MajorResearchAgent → majors_latest.json
                                        ↓
                            CareerAnalysisAgent.process_query()
                                        ↓
                        ┌───────────────┴───────────────┐
                        ↓                               ↓
                identify_careers()            analyze_career_simple()
                (LLM识别3个职业)                      ↓
                                        ┌──────────────┴──────────────┐
                                        ↓                             ↓
                            生成描述 + 收集资源           查询数据库
                            (LLM + DuckDuckGo)         (TF-IDF + SQLite)
                                        ↓                             ↓
                                    description              salary + job_examples
                                    resources                db_match_count
                                        └──────────────┬──────────────┘
                                                       ↓
                                            careers_latest.json
```

## 使用方法

### 1. 单个职业分析

```python
from backend.agents.career_analysis_agent import create_career_analysis_agent

agent = create_career_analysis_agent()

# 分析单个职业
result = await agent.analyze_career_simple(
    career_title="Software Engineer",
    major_name="Computer Science"
)

print(result['description'])
print(f"Salary: ${result['salary']['min']} - ${result['salary']['max']}")
print(f"Resources: {len(result['resources'])} URLs")
print(f"Job Examples: {len(result['job_examples'])} from DB")
```

### 2. 完整工作流（从JSON）

```python
# 读取 majors_latest.json，为每个专业生成职业分析
results = await agent.process_query()

# 结果自动保存到:
# - backend/database/careers_<timestamp>.json
# - backend/database/careers_latest.json
```

## 依赖要求

### 必需
- `spoon_ai` - LLM集成
- `duckduckgo-search` 或 `ddgs` - Web搜索
- `beautifulsoup4` - HTML解析
- `httpx` - HTTP客户端

### 可选（数据库功能）
- `scikit-learn` - TF-IDF相似度计算
- SQLite数据库文件: `backend/agents/job_info.db`

**注意**: 如果未安装 scikit-learn，数据库功能将被禁用，但其他功能仍正常工作。

## 测试

```bash
# 测试单个职业分析
python tests/test_integrated_career_agent.py

# 测试完整结构输出
python tests/test_final_structure.py

# 测试完整工作流（需要先生成 major JSON）
python tests/major_research_test.py      # 生成 majors
python tests/career_analysis_test.py     # 生成 careers
```

## 数据库设置

如果要使用真实薪资数据功能，需要准备 SQLite 数据库：

```sql
-- job_info.db 结构
CREATE TABLE jobs (
    "Job Title" TEXT,
    "Company" TEXT,
    "Salary Range" TEXT,
    "Job Description" TEXT
);
```

数据库路径：`backend/agents/job_info.db`

## 优势

✅ **完整性**: 结合了Web资源和本地数据库  
✅ **准确性**: 使用真实薪资数据，避免LLM幻觉  
✅ **可扩展**: 易于添加新的数据源  
✅ **容错性**: 各模块独立，失败不影响其他功能  
✅ **性能**: 使用异步处理和数据库索引  

## 下一步

1. ✅ 集成完成
2. ⏳ 添加更多职业数据到数据库
3. ⏳ 前端展示集成数据
4. ⏳ 添加缓存机制提高性能

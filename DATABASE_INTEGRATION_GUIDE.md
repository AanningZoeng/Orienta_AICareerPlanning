# Career Agent 数据库集成 - 完整指南

## ✅ 已完成的功能

CareerAnalysisAgent 现在完全集成了数据库功能：

1. **LLM 生成描述** - 使用 Gemini 生成职业描述
2. **Web 资源搜索** - 通过 DuckDuckGo 收集在线资源
3. **数据库薪资查询** - 使用 TF-IDF 相似度匹配真实职位数据
4. **职位示例提取** - 从数据库中提取匹配的职位信息

## 📋 使用流程

### 方案 A: 完整端到端测试（推荐）

```bash
# 1. 创建示例数据库（30+ 职位）
python tests\create_sample_db.py

# 2. 安装依赖
pip install scikit-learn

# 3. 运行端到端测试（自动生成 major → career）
python tests\test_end_to_end.py

# 4. 验证JSON结构
python tests\verify_json_structure.py
```

### 方案 B: 分步测试

```bash
# 1. 创建示例数据库
python tests\create_sample_db.py

# 2. 测试数据库功能
python tests\test_agent2_database.py

# 3. 生成专业数据
python tests\major_research_test.py

# 4. 生成职业数据（集成数据库）
python tests\career_analysis_test.py

# 5. 验证结构
python tests\verify_json_structure.py
```

## 📊 输出结构

生成的 `careers_latest.json` 结构：

```json
{
  "timestamp": "2025-11-23T12:34:56",
  "source_timestamp": "20251123_123400",
  "user_query": "用户的原始查询",
  "careers": {
    "Computer Science": {
      "Software Engineer": {
        "description": "Software Engineer designs, develops, tests...",
        "resources": [
          "https://example.com/resource1",
          "https://example.com/resource2"
        ],
        "salary": {
          "min": 120000,
          "max": 180000,
          "currency": "USD"
        },
        "job_examples": [
          {
            "job_title": "Software Engineer",
            "company": "Google",
            "description": "Design and develop scalable...",
            "salary_range": "$120k - $180k"
          }
        ],
        "db_match_count": 5
      },
      "Data Scientist": {
        ...
      }
    },
    "Mathematics": {
      ...
    }
  }
}
```

## 🔍 关键实现细节

### 1. TF-IDF 相似度匹配

```python
# career_analysis_agent.py 中的 _vec_similarity() 方法
# 使用 TF-IDF 向量化计算职位标题相似度
# 阈值默认 0.2，可以调整以获得更多或更少匹配
```

### 2. 薪资解析

```python
# _parse_salary() 方法解析各种格式:
# "$100k - $150k" → [100000, 150000]
# "$80,000 - $120,000" → [80000, 120000]
# "100k-150k" → [100000, 150000]
```

### 3. 数据库查询流程

```python
# _fetch_job_db_data() 流程:
1. 使用 TF-IDF 找到相似职位标题
2. 从数据库查询匹配的职位
3. 解析所有薪资范围
4. 计算 min/max
5. 返回职位示例（最多5个）
```

## 🧪 测试文件说明

| 文件 | 功能 | 用途 |
|------|------|------|
| `create_sample_db.py` | 创建示例数据库 | 快速生成测试数据 |
| `test_agent2_database.py` | 测试数据库功能 | 验证 TF-IDF、薪资解析等 |
| `test_integrated_career_agent.py` | 测试单个职业分析 | 检查集成是否工作 |
| `test_end_to_end.py` | 完整流程测试 | major → career 全流程 |
| `verify_json_structure.py` | 验证JSON结构 | 确保输出格式正确 |

## ⚙️ 配置选项

### 自定义数据库路径

```python
from backend.agents.career_analysis_agent import CareerAnalysisAgent

# 使用自定义数据库
agent = CareerAnalysisAgent(
    llm_agent=None,  # 或提供 LLM agent
    db_path="/path/to/your/job_info.db"
)
```

### 调整相似度阈值

编辑 `career_analysis_agent.py`:

```python
# 在 _fetch_job_db_data() 中:
similar_jobs = self._vec_similarity(target_job, threshold=0.2)  # 调整此值
```

- 阈值更低 (0.1) = 更多匹配（可能不太相关）
- 阈值更高 (0.3) = 更少匹配（更精确）

## 📈 性能优化

### 数据库索引

如果数据库很大，添加索引：

```sql
CREATE INDEX idx_job_title ON jobs("Job Title");
CREATE INDEX idx_company ON jobs(Company);
```

### 缓存

考虑缓存 TF-IDF 结果以提高性能：

```python
# 可以在 __init__ 中预计算所有职位标题的向量
```

## 🚨 故障排查

### 问题: `db_match_count: 0`

**原因**:
1. 数据库文件不存在
2. scikit-learn 未安装
3. 数据库中没有相关职位

**解决方案**:
```bash
# 1. 检查数据库
python tests\test_agent2_database.py

# 2. 安装 scikit-learn
pip install scikit-learn

# 3. 添加更多数据
# 编辑 create_sample_db.py 添加职位
python tests\create_sample_db.py
```

### 问题: 薪资全是 0

**原因**: 数据库中的薪资格式无法解析

**解决方案**:
确保薪资格式为：`$XXk - $YYk` 或 `$XX,XXX - $YY,YYY`

### 问题: 相似度匹配不准确

**解决方案**: 调整阈值或使用更精确的职位标题

## 📝 添加自定义职位数据

编辑 `tests/create_sample_db.py`:

```python
sample_jobs = [
    ("Job Title", "Company", "$XXk - $YYk", "Job description"),
    ("Software Engineer", "Your Company", "$100k - $150k", "Build amazing products"),
    # 添加更多...
]
```

重新运行：
```bash
python tests\create_sample_db.py
```

## ✨ 未来增强

- [ ] 支持更多数据源（LinkedIn API, Indeed API）
- [ ] 添加地理位置过滤
- [ ] 支持经验等级匹配
- [ ] 缓存机制
- [ ] 定期更新薪资数据

## 📚 相关文档

- [CAREER_AGENT_INTEGRATION.md](CAREER_AGENT_INTEGRATION.md) - 架构设计
- [AGENT2_TESTING_GUIDE.md](AGENT2_TESTING_GUIDE.md) - 测试指南
- [AGENTS.md](AGENTS.md) - 多智能体架构

---

**状态**: ✅ 生产就绪  
**最后更新**: 2025-11-23

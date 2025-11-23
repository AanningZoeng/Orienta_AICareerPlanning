# Agent2 数据库功能测试指南

## 快速开始

### 步骤 1: 创建示例数据库

```bash
cd d:\python\Orienta_AICareerPlanning
python tests\create_sample_db.py
```

这将创建 `backend/agents/job_info.db`，包含 30+ 个示例职位。

### 步骤 2: 安装依赖

```bash
pip install scikit-learn
```

如果已安装，跳过此步骤。

### 步骤 3: 测试数据库功能

```bash
python tests\test_agent2_database.py
```

### 步骤 4: 测试完整集成

```bash
python tests\test_integrated_career_agent.py
```

## 测试内容

### `create_sample_db.py`
- ✅ 创建 SQLite 数据库
- ✅ 插入 30+ 示例职位数据
- ✅ 涵盖多个领域：软件工程、数据科学、产品管理等

### `test_agent2_database.py`
- ✅ 检查依赖（scikit-learn, sqlite3）
- ✅ 验证数据库文件存在
- ✅ 分析数据库内容
- ✅ 测试 TF-IDF 相似度匹配
- ✅ 测试薪资解析
- ✅ 测试完整数据库查询
- ✅ 测试集成分析

### `test_integrated_career_agent.py`
- ✅ 诊断数据库状态
- ✅ 测试完整职业分析
- ✅ 验证输出结构

## 示例输出

### 成功的数据库查询
```json
{
  "description": "Software Engineer designs and develops...",
  "resources": ["URL1", "URL2", ...],
  "salary": {
    "min": 120000,
    "max": 180000,
    "currency": "USD"
  },
  "job_examples": [
    {
      "job_title": "Software Engineer",
      "company": "Google",
      "salary_range": "$120k - $180k",
      "description": "Design and develop..."
    }
  ],
  "db_match_count": 5
}
```

## 故障排查

### 问题 1: `DB matches: 0`

**原因**：
- 数据库文件不存在
- scikit-learn 未安装
- 数据库中没有匹配的职位

**解决方案**：
```bash
# 1. 创建数据库
python tests\create_sample_db.py

# 2. 安装依赖
pip install scikit-learn

# 3. 重新测试
python tests\test_agent2_database.py
```

### 问题 2: `scikit-learn not installed`

**解决方案**：
```bash
pip install scikit-learn
```

### 问题 3: `Database file not found`

**检查路径**：
- 期望位置：`backend/agents/job_info.db`
- 或运行：`python tests\create_sample_db.py` 自动创建

## 数据库结构

```sql
CREATE TABLE jobs (
    "Job Title" TEXT,
    Company TEXT,
    "Salary Range" TEXT,
    "Job Description" TEXT
);
```

## 添加自定义数据

编辑 `create_sample_db.py` 中的 `sample_jobs` 列表：

```python
sample_jobs = [
    ("Job Title", "Company", "$XXk - $YYk", "Description"),
    # 添加更多职位...
]
```

然后重新运行：
```bash
python tests\create_sample_db.py
```

## 验证数据库

使用 SQLite 命令行工具：
```bash
sqlite3 backend/agents/job_info.db

sqlite> SELECT COUNT(*) FROM jobs;
sqlite> SELECT * FROM jobs LIMIT 5;
sqlite> .exit
```

或使用 Python：
```python
import sqlite3
conn = sqlite3.connect('backend/agents/job_info.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM jobs')
print(cursor.fetchone()[0])
conn.close()
```

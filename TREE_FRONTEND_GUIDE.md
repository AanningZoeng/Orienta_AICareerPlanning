# 树形前端使用说明

## 概述

前端已重构为**树形交互结构**，用户从根节点开始，逐步展开职业路径树。

## 树形结构

```
┌─────────────────────────────────────────────────────────────┐
│                      ROOT NODE (根节点)                       │
│              用户输入自我介绍和兴趣描述                         │
│                 点击后调用 MajorResearchAgent                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │               │
    ┌───▼───┐      ┌───▼───┐      ┌───▼───┐
    │ Major │      │ Major │      │ Major │
    │   1   │      │   2   │      │   3   │
    └───┬───┘      └───┬───┘      └───────┘
        │              │
        │ (点击展开)   │
        │              │
  ┌─────┼─────┐   ┌────┼────┐
  │     │     │   │    │    │
┌─▼─┐ ┌─▼─┐ ┌─▼─┐ Career Career
│C1 │ │C2 │ │C3 │  (调用 CareerAnalysisAgent)
└─┬─┘ └───┘ └───┘
  │
  │ (点击展开)
  │
┌─┴─┐ ┌───┐ ┌───┐
│F1 │ │F2 │ │F3 │  Future Paths
└───┘ └───┘ └───┘  (调用 FuturePathAgent - 暂未实现)
```

## 节点类型

### 1. **Root Node (根节点)** - 蓝色渐变
- **功能**: 用户输入交互点
- **点击行为**: 
  - 首次点击: 弹出表单，输入自我介绍
  - 提交后: 调用 `POST /api/research-majors`
  - 已展开: 显示用户输入内容

### 2. **Major Nodes (专业节点)** - 紫色渐变
- **数量**: 2-3 个 (根据 MajorResearchAgent 配置)
- **点击行为**:
  - 首次点击: 调用 `POST /api/analyze-careers` 展开该专业的职业
  - 已展开: 显示 description + resources
- **数据结构**:
  ```json
  {
    "description": "LLM生成的2-4句专业介绍",
    "resources": ["url1", "url2", ...]
  }
  ```

### 3. **Career Nodes (职业节点)** - 绿色渐变
- **数量**: 每个 major 3 个
- **点击行为**:
  - 首次点击: 调用 FuturePathAgent (暂未实现，使用 mock 数据)
  - 已展开: 显示 description + resources
- **数据结构**:
  ```json
  {
    "description": "LLM生成的职业描述",
    "resources": ["url1", "url2", ...]
  }
  ```

### 4. **Future Path Nodes (未来路径节点)** - 黄色渐变
- **数量**: 每个 career 3 个
- **点击行为**: 显示未来发展预测 (mock 数据)

## 交互流程

### 步骤 1: 启动服务器
```powershell
cd d:\python\Orienta_AICareerPlanning
python backend\api\server.py
```

### 步骤 2: 打开浏览器
访问: `http://localhost:5000/`

### 步骤 3: 与根节点交互
1. 页面加载后，会看到一个蓝色透明的根节点
2. **点击根节点**，弹出输入表单
3. 输入自我介绍，例如:
   ```
   I love technology and solving complex problems. 
   I'm interested in AI and data science.
   ```
4. 点击 "Generate My Career Path"

### 步骤 4: 查看专业推荐
- 系统调用 MajorResearchAgent
- 树中展开 2-3 个专业节点
- 每个专业节点显示名称

### 步骤 5: 展开职业路径
1. **点击任意专业节点**
2. 系统调用 CareerAnalysisAgent
3. 该专业下展开 3 个职业节点

### 步骤 6: 查看详情
- **点击已展开的节点**: 弹出模态框显示详情
  - **Description**: LLM 生成的描述
  - **Resources**: 网络搜索到的相关链接

### 步骤 7: 继续展开
- 点击职业节点可展开未来路径 (当前为 mock 数据)

## 视觉特性

### 节点样式
- **透明材质**: 所有节点使用半透明渐变色
- **毛玻璃效果**: backdrop-filter blur
- **阴影**: drop-shadow 滤镜
- **悬停反馈**: 鼠标悬停时节点变亮

### 连接线
- **曲线路径**: 使用 SVG cubic bezier 曲线
- **半透明**: 淡紫色，透明度 0.3

### 扩展指示器
- **小圆点**: 节点底部显示 +/- 符号
- **颜色**:
  - 绿色: 已展开
  - 灰色: 未展开

## API 端点

### `POST /api/research-majors`
```json
Request:
{
  "query": "用户自我介绍"
}

Response:
{
  "majors": {
    "Computer Science": {
      "description": "...",
      "resources": ["url1", ...]
    }
  }
}
```

### `POST /api/analyze-careers`
```json
Request:
{
  "major_name": "Computer Science"
}

Response:
{
  "careers": {
    "Software Engineer": {
      "description": "...",
      "resources": ["url1", ...]
    }
  }
}
```

## 已知限制

1. **FuturePathAgent 未实现**: 当前使用 mock 数据
2. **CareerAnalysisAgent 处理所有专业**: 
   - 当前实现中，每次点击专业都会处理 `majors_latest.json` 中的所有专业
   - 可优化为只处理被点击的专业

## 样式文件

- `frontend/index.html`: 树形结构 SVG 容器
- `frontend/scripts/tree-engine.js`: 树形可视化引擎
- `frontend/scripts/main.js`: 主逻辑和 API 调用
- `frontend/styles/main.css`: 树形节点样式

## 测试建议

1. **测试根节点交互**:
   - 点击根节点 → 输入表单显示
   - 提交 → 专业节点出现

2. **测试数据流**:
   - 检查 `backend/database/majors_latest.json`
   - 检查 `backend/database/careers_latest.json`

3. **测试模态框**:
   - 点击已展开节点
   - 验证 description 和 resources 显示

4. **测试响应式**:
   - 调整浏览器窗口大小
   - 验证 SVG 自适应

## 下一步优化

1. ✅ 实现 FuturePathAgent
2. ✅ 优化 CareerAnalysisAgent 按需加载
3. ✅ 添加节点搜索功能
4. ✅ 添加路径导出功能
5. ✅ 动画过渡效果

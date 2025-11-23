# 前端使用说明

## 🎨 交互式泡泡树可视化系统

这是一个基于SVG的多Agent职业规划可视化前端，支持实时Agent调用和动态节点展开。

## 📁 文件结构

```
frontend/
├── index.html              # 主页面（已更新为中文版）
├── scripts/
│   ├── bubble-engine.js    # SVG泡泡树引擎（核心渲染逻辑）
│   ├── detail-view.js      # 模态框管理器（节点详情显示）
│   └── main.js            # 应用控制器（API调用 + 事件处理）
└── styles/
    ├── main.css           # 全局样式
    ├── bubbles.css        # 泡泡节点样式
    └── details.css        # 模态框样式
```

## 🚀 启动方式

### 方法1：通过Flask服务器（推荐）

1. **启动后端API服务器**:
   ```powershell
   cd d:\python\Orienta_AICareerPlanning
   python backend/api/server.py
   ```

2. **访问前端页面**:
   ```
   http://localhost:5000/index.html
   ```

### 方法2：使用Python简易服务器

```powershell
cd d:\python\Orienta_AICareerPlanning\frontend
python -m http.server 8080
```

然后访问: `http://localhost:8080/index.html`

> ⚠️ **注意**: 使用此方法时，需要确保后端API服务器运行在 `http://localhost:5000`

### 方法3：使用Live Server（VS Code）

1. 安装VS Code扩展: `Live Server`
2. 右键点击 `index.html` → "Open with Live Server"

## 🎯 功能特性

### 1. **查询输入**
- 用户在首页输入职业兴趣和目标
- 示例: "我喜欢编程、算法和数学。什么专业适合我？"

### 2. **Major节点展示**
- AI分析后显示根节点（查询）+ 专业节点
- 圆形泡泡布局，带渐变色和发光效果
- 平滑动画从中心扩散

### 3. **交互式展开**
- **点击根节点**: 显示查询详情
- **点击Major节点**: 
  - 首次点击 → 显示专业详情
  - 再次点击 → 调用Career Analysis Agent，展开职业节点
- **点击Career节点**: 显示职业详情（薪资、案例、资源）

### 4. **模态框详情**
- 专业详情: 简介、核心课程、学习资源、推荐院校
- 职业详情: 简介、薪资范围、真实职位案例、学习资源
- 支持ESC键关闭、点击遮罩关闭

### 5. **Agent工作流可视化**
- Loading overlay显示当前Agent状态
- 步骤指示器:
  - 📚 Major Research Agent
  - 💼 Career Analysis Agent
- 实时状态更新: ⏳ 工作中 → ✅ 完成

## 🔌 API端点

前端调用以下后端API:

### `/api/major-research` (POST)
**请求**:
```json
{
  "query": "用户的职业兴趣查询"
}
```

**响应**:
```json
{
  "success": true,
  "majors": [
    {
      "name": "计算机科学 (Computer Science)",
      "description": "...",
      "core_courses": ["数据结构", "算法设计", ...],
      "resources": [...],
      "universities": [...]
    }
  ]
}
```

### `/api/career-analysis` (POST)
**请求**:
```json
{
  "major_name": "计算机科学 (Computer Science)"
}
```

**响应**:
```json
{
  "success": true,
  "careers": [
    {
      "title": "软件工程师",
      "description": "...",
      "salary": { "min": 80000, "max": 220000, "currency": "USD" },
      "resources": [...],
      "job_examples": [...],
      "db_match_count": 523
    }
  ]
}
```

## 🎨 视觉设计

### 节点类型渐变色
- **根节点 (Root)**: 紫蓝渐变 `#667eea → #764ba2`
- **专业节点 (Major)**: 粉红渐变 `#f093fb → #f5576c`
- **职业节点 (Career)**: 青蓝渐变 `#4facfe → #00f2fe`

### 交互效果
- **悬停 (Hover)**: 发光滤镜 + 缩放
- **点击 (Click)**: 触发模态框 + Agent调用
- **动画 (Animation)**: easeOutCubic缓动，600ms

## 🧪 开发模式（Mock数据）

如果API服务器未启动或调用失败，前端会自动切换到Mock数据模式:

- `getMockMajorsData()`: 返回3个模拟专业
- `getMockCareersData()`: 返回每个专业2-3个模拟职业

这允许前端独立开发和测试，无需依赖后端。

## 📦 导出功能

点击"导出数据"按钮可下载完整的职业规划数据:

```json
{
  "query": "用户查询",
  "majors": [...],
  "careers": {...},
  "tree": {
    "nodes": [...],
    "links": [...]
  }
}
```

## 🔧 自定义配置

### 修改API地址
在 `main.js` 中:

```javascript
class CareerPlanningApp {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000/api';  // 修改这里
        // ...
    }
}
```

### 调整节点大小
在 `bubble-engine.js` 中:

```javascript
this.nodeConfig = {
    root: { radius: 60, ... },    // 根节点半径
    major: { radius: 50, ... },   // 专业节点半径
    career: { radius: 40, ... }   // 职业节点半径
};
```

### 修改布局间距
```javascript
this.levelSpacing = 280;  // 层级垂直间距
```

## 🐛 调试技巧

### 1. 打开浏览器开发者工具 (F12)
查看Console输出:
- `✅ AI Career Planning App initialized` - 应用初始化成功
- `Node clicked: ...` - 节点点击事件
- `[ERROR] ...` - API调用错误

### 2. 检查网络请求 (Network Tab)
- 查看API调用状态码
- 检查请求/响应数据格式

### 3. 常见问题

**Q: 点击节点没反应？**
- 检查Console是否有JavaScript错误
- 确认`bubble-engine.js`、`detail-view.js`、`main.js`已正确加载

**Q: API调用失败？**
- 确认后端服务器运行在 `http://localhost:5000`
- 检查CORS配置（Flask已启用CORS）
- 查看后端Console的错误日志

**Q: 模态框样式异常？**
- 检查`details.css`是否正确加载
- 清除浏览器缓存后刷新

## 📝 技术栈

- **纯JavaScript ES6+** (无框架依赖)
- **SVG** (可缩放矢量图形)
- **CSS3** (渐变、动画、滤镜)
- **Fetch API** (异步HTTP请求)
- **Async/Await** (异步流程控制)

## 🚀 性能优化

1. **节点渲染**: 使用SVG而非Canvas，支持硬件加速
2. **动画**: RequestAnimationFrame确保60fps
3. **数据缓存**: 已展开的Career数据会缓存，避免重复API调用
4. **延迟导入**: 模块化设计，按需加载

## 📚 下一步扩展

- [ ] 添加Future Path Agent第三层节点
- [ ] 实现节点搜索和过滤功能
- [ ] 添加全屏模式和缩放功能
- [ ] 支持多语言切换
- [ ] 实现数据持久化（LocalStorage）
- [ ] 添加用户偏好设置面板

## 💡 最佳实践

1. **先运行一次完整workflow**: 使用Major Research Agent生成`majors_latest.json`，再让Career Analysis Agent读取
2. **测试Mock数据**: 在后端未准备好时，可以先测试前端交互逻辑
3. **监控Console日志**: 所有关键操作都有日志输出
4. **渐进式增强**: 先确保基础功能，再添加高级特性

---

**Created by**: AI Career Planning System  
**Version**: 2.0 - SVG Bubble Tree Edition  
**Last Updated**: 2025-01-23

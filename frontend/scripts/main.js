/**
 * Main Application Controller
 * 
 * 协调前端UI、API调用和多Agent交互
 */

class CareerPlanningApp {
    constructor() {
        // API配置
        this.apiBaseUrl = 'http://localhost:5000/api';
        
        // 初始化组件
        this.treeEngine = new BubbleTreeEngine('treeCanvas');
        this.detailView = new DetailViewManager('detailModal');
        
        // UI元素
        this.querySection = document.getElementById('querySection');
        this.treeSection = document.getElementById('treeSection');
        this.queryForm = document.getElementById('queryForm');
        this.submitBtn = document.getElementById('submitBtn');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.newQueryBtn = document.getElementById('newQueryBtn');
        this.exportBtn = document.getElementById('exportBtn');
        
        // 当前查询数据
        this.currentQuery = null;
        this.majorsData = null;
        this.majorsFullData = {};  // 存储完整的major详细信息
        this.careersData = {};
        this.futurePathsData = {};  // 存储future path数据
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // 表单提交
        this.queryForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleQuerySubmit();
        });
        
        // 树节点事件
        this.treeEngine.onNodeClick = (node) => this.handleNodeClick(node);
        this.treeEngine.onNodeHover = (node) => this.handleNodeHover(node);
        
        // 操作按钮
        this.newQueryBtn.addEventListener('click', () => this.resetQuery());
        this.exportBtn.addEventListener('click', () => this.exportData());
    }
    
    /**
     * 处理查询提交
     */
    async handleQuerySubmit() {
        const query = document.getElementById('userQuery').value.trim();
        if (!query) return;
        
        this.currentQuery = query;
        this.showLoading('major', 'Major Research Agent is analyzing your interests...');
        
        try {
            // 调用Major Research Agent
            const majorsResponse = await this.callMajorResearchAgent(query);
            
            if (majorsResponse.success) {
                this.majorsData = majorsResponse.majors;
                
                // 存储完整的major数据（包括从JSON读取的详细信息）
                this.majorsFullData = {};
                this.majorsData.forEach(major => {
                    this.majorsFullData[major.name] = major;
                });
                
                // 切换到树视图
                this.querySection.style.display = 'none';
                this.treeSection.style.display = 'block';
                
                // 初始化树
                this.treeEngine.initializeTree(query);
                
                // 添加major节点
                await this.delay(500);
                this.treeEngine.addMajors(this.majorsData);
                
                this.updateLoadingStep('major', 'complete', '✅ Major research completed!');
                await this.delay(1000);
                this.hideLoading();
            } else {
                throw new Error(majorsResponse.error || 'Major research failed');
            }
        } catch (error) {
            console.error('Query submission error:', error);
            this.hideLoading();
            this.showError('Query failed: ' + error.message);
        }
    }
    
    /**
     * 处理节点点击
     */
    async handleNodeClick(node) {
        console.log('Node clicked:', node);
        
        if (node.type === 'root') {
            this.detailView.showRootDetails(node);
        } 
        else if (node.type === 'major') {
            // 只显示major详情，不自动展开
            this.detailView.showMajorDetails(node);
            
            // 等待DOM渲染完成后，绑定展开按钮事件
            await this.delay(100);
            const expandBtn = document.querySelector('.btn-expand-careers');
            if (expandBtn) {
                expandBtn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    const majorId = expandBtn.dataset.majorId;
                    const majorName = expandBtn.dataset.majorName;
                    
                    // 关闭模态框
                    this.detailView.hide();
                    await this.delay(300);
                    
                    // 展开职业路径
                    const majorNode = this.treeEngine.getNode(majorId);
                    if (majorNode) {
                        await this.expandMajorWithCareers(majorNode);
                    }
                });
            }
        } 
        else if (node.type === 'career') {
            // 显示career详情，并绑定展开future path按钮
            this.detailView.showCareerDetails(node);
            
            // 等待DOM渲染完成后，绑定展开按钮事件
            await this.delay(100);
            const expandBtn = document.querySelector('.btn-expand-future');
            if (expandBtn) {
                expandBtn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    const careerId = expandBtn.dataset.careerId;
                    const careerTitle = expandBtn.dataset.careerTitle;
                    
                    // 关闭模态框
                    this.detailView.hide();
                    await this.delay(300);
                    
                    // 展开future path
                    const careerNode = this.treeEngine.getNode(careerId);
                    if (careerNode) {
                        await this.expandCareerWithFuturePath(careerNode);
                    }
                });
            }
        }
        else if (node.type === 'future') {
            this.detailView.showFutureDetails(node);
        }
    }
    
    /**
     * 处理节点悬停
     */
    handleNodeHover(node) {
        // 可以添加tooltip显示
        console.log('Node hovered:', node.name);
    }
    
    /**
     * 展开Major节点并加载Career数据
     */
    async expandMajorWithCareers(majorNode) {
        const majorName = majorNode.data.name;
        
        this.showLoading('career', `Career Analysis Agent is analyzing career paths for "${majorName}"...`);
        
        try {
            // 检查是否已有缓存
            if (!this.careersData[majorName]) {
                const careersResponse = await this.callCareerAnalysisAgent(majorName);
                
                if (careersResponse.success) {
                    this.careersData[majorName] = careersResponse.careers;
                } else {
                    throw new Error(careersResponse.error || 'Career analysis failed');
                }
            }
            
            // 展开节点
            const careers = this.careersData[majorName];
            this.treeEngine.expandMajor(majorNode.id, careers);
            
            this.updateLoadingStep('career', 'complete', '✅ Career analysis completed!');
            await this.delay(1000);
            this.hideLoading();
        } catch (error) {
            console.error('Career expansion error:', error);
            this.hideLoading();
            this.showError('Career analysis failed: ' + error.message);
        }
    }
    
    /**
     * 展开Career节点并加载Future Path数据
     */
    async expandCareerWithFuturePath(careerNode) {
        const careerTitle = careerNode.data.title;
        
        this.showLoading('future', `Future Path Agent is analyzing career progression for "${careerTitle}"...`);
        
        try {
            // 检查是否已有缓存
            if (!this.futurePathsData[careerTitle]) {
                const futureResponse = await this.callFuturePathAgent(careerTitle);
                
                if (futureResponse.success) {
                    this.futurePathsData[careerTitle] = futureResponse.future_path;
                } else {
                    throw new Error(futureResponse.error || 'Future path analysis failed');
                }
            }
            
            // 展开节点
            const futurePath = this.futurePathsData[careerTitle];
            this.treeEngine.expandCareer(careerNode.id, futurePath);
            
            this.updateLoadingStep('future', 'complete', '✅ Future path analysis completed!');
            await this.delay(1000);
            this.hideLoading();
        } catch (error) {
            console.error('Future path expansion error:', error);
            this.hideLoading();
            this.showError('Career analysis failed: ' + error.message);
        }
    }
    
    /**
     * 展开Career节点并加载Future Path数据
     */
    async expandCareerWithFuturePath(careerNode) {
        const careerTitle = careerNode.data.title;
        
        this.showLoading('future', `Future Path Agent is analyzing career progression for "${careerTitle}"...`);
        
        try {
            // 检查是否已有缓存
            if (!this.futurePathsData[careerTitle]) {
                const futureResponse = await this.callFuturePathAgent(careerTitle);
                
                if (futureResponse.success) {
                    this.futurePathsData[careerTitle] = futureResponse.future_path;
                } else {
                    throw new Error(futureResponse.error || 'Future path analysis failed');
                }
            }
            
            // 展开节点
            const futurePath = this.futurePathsData[careerTitle];
            this.treeEngine.expandCareer(careerNode.id, futurePath);
            
            this.updateLoadingStep('future', 'complete', '✅ Future path analysis completed!');
            await this.delay(1000);
            this.hideLoading();
        } catch (error) {
            console.error('Future path expansion error:', error);
            this.hideLoading();
            this.showError('Future path analysis failed: ' + error.message);
        }
    }
    
    /**
     * API调用: Major Research Agent
     */
    async callMajorResearchAgent(query) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/major-research`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            
            // 如果API失败，使用模拟数据
            console.warn('Using mock data for development');
            return this.getMockMajorsData(query);
        }
    }
    
    /**
     * API调用: Career Analysis Agent
     */
    async callCareerAnalysisAgent(majorName) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/career-analysis`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ major_name: majorName })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            
            // 如果API失败，使用模拟数据
            console.warn('Using mock data for development');
            return this.getMockCareersData(majorName);
        }
    }
    
    /**
     * API调用: Future Path Agent
     */
    async callFuturePathAgent(careerTitle) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/future-path-analysis`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ career_title: careerTitle, years: 5 })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            
            // 如果API失败，使用模拟数据
            console.warn('Using mock data for development');
            return this.getMockCareersData(majorName);
        }
    }
    
    /**
     * API调用: Future Path Agent
     */
    async callFuturePathAgent(careerTitle) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/future-path-analysis`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ career_title: careerTitle, years: 5 })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            
            // 如果API失败，使用模拟数据
            console.warn('Using mock data for development');
            return this.getMockFuturePathData(careerTitle);
        }
    }
    
    /**
     * 模拟数据 - Future Path
     */
    getMockFuturePathData(careerTitle) {
        return {
            success: true,
            future_path: {
                id: `${careerTitle.toLowerCase().replace(/\s+/g, '_')}_future`,
                career: careerTitle,
                timeframe: "5 years",
                statistics: {
                    promoted: {
                        percentage: 45,
                        description: "45% of professionals were promoted to higher positions"
                    },
                    same_role: {
                        percentage: 30,
                        description: "30% remained in similar roles with increased responsibility"
                    },
                    changed_company: {
                        percentage: 15,
                        description: "15% moved to different companies for better opportunities"
                    },
                    changed_field: {
                        percentage: 10,
                        description: "10% transitioned to different fields or industries"
                    }
                },
                common_progressions: [
                    `Senior ${careerTitle} (35%)`,
                    `Lead/Principal ${careerTitle} (25%)`,
                    "Engineering Manager (20%)",
                    "Technical Architect (15%)",
                    "Director of Engineering (5%)"
                ],
                insights: [
                    "Strong technical skills are essential for advancement",
                    "Leadership and communication skills become increasingly important",
                    "Continuous learning and staying updated with industry trends is critical",
                    "Building a professional network opens up more opportunities"
                ],
                resources: [
                    { title: "Career Progression Guide", url: "https://example.com/career-guide", type: "article" },
                    { title: "Leadership Development Course", url: "https://example.com/leadership", type: "course" }
                ]
            }
        };
    }
    
    /**
     * 模拟数据 - Major Research
     */
    getMockMajorsData(query) {
        return {
            success: true,
            majors: [
                {
                    name: "计算机科学 (Computer Science)",
                    description: "计算机科学专业研究计算机系统、软件开发、算法设计和人工智能等领域。",
                    core_courses: ["数据结构", "算法设计", "操作系统", "计算机网络", "数据库系统"],
                    resources: [
                        { title: "MIT计算机科学课程", url: "https://ocw.mit.edu/courses/electrical-engineering-and-computer-science/", type: "course" },
                        { title: "算法导论", url: "https://mitpress.mit.edu/books/introduction-algorithms", type: "book" }
                    ],
                    universities: [
                        { name: "MIT", ranking: 1 },
                        { name: "Stanford University", ranking: 2 }
                    ]
                },
                {
                    name: "数据科学 (Data Science)",
                    description: "数据科学结合统计学、机器学习和编程技能，从海量数据中提取洞察。",
                    core_courses: ["统计学", "机器学习", "数据可视化", "大数据技术", "Python编程"],
                    resources: [
                        { title: "Kaggle数据科学课程", url: "https://www.kaggle.com/learn", type: "course" },
                        { title: "数据科学手册", url: "https://jakevdp.github.io/PythonDataScienceHandbook/", type: "book" }
                    ],
                    universities: [
                        { name: "UC Berkeley", ranking: 3 },
                        { name: "Harvard University", ranking: 4 }
                    ]
                },
                {
                    name: "人工智能 (Artificial Intelligence)",
                    description: "人工智能专业专注于机器学习、深度学习、自然语言处理和计算机视觉等前沿技术。",
                    core_courses: ["深度学习", "自然语言处理", "计算机视觉", "强化学习", "AI伦理"],
                    resources: [
                        { title: "Stanford CS229机器学习", url: "http://cs229.stanford.edu/", type: "course" },
                        { title: "深度学习", url: "https://www.deeplearningbook.org/", type: "book" }
                    ],
                    universities: [
                        { name: "Carnegie Mellon University", ranking: 1 },
                        { name: "Stanford University", ranking: 2 }
                    ]
                }
            ]
        };
    }
    
    /**
     * 模拟数据 - Future Path
     */
    getMockFuturePathData(careerTitle) {
        return {
            success: true,
            future_path: {
                id: `${careerTitle.toLowerCase().replace(/\s+/g, '_')}_future`,
                career: careerTitle,
                timeframe: "5 years",
                statistics: {
                    promoted: {
                        percentage: 45,
                        description: "45% of professionals were promoted to higher positions"
                    },
                    same_role: {
                        percentage: 30,
                        description: "30% remained in similar roles with increased responsibility"
                    },
                    changed_company: {
                        percentage: 15,
                        description: "15% moved to different companies for better opportunities"
                    },
                    changed_field: {
                        percentage: 10,
                        description: "10% transitioned to different fields or industries"
                    }
                },
                common_progressions: [
                    "Senior ${careerTitle} (35%)",
                    "Lead/Principal ${careerTitle} (25%)",
                    "Engineering Manager (20%)",
                    "Technical Architect (15%)",
                    "Director of Engineering (5%)"
                ],
                insights: [
                    "Strong technical skills are essential for advancement",
                    "Leadership and communication skills become increasingly important",
                    "Continuous learning and staying updated with industry trends is critical",
                    "Building a professional network opens up more opportunities"
                ],
                resources: [
                    { title: "Career Progression Guide", url: "https://example.com/career-guide", type: "article" },
                    { title: "Leadership Development Course", url: "https://example.com/leadership", type: "course" }
                ]
            }
        };
    }
    
    /**
     * 模拟数据 - Career Analysis
     */
    getMockCareersData(majorName) {
        const careersMap = {
            "计算机科学 (Computer Science)": [
                {
                    title: "软件工程师",
                    description: "设计、开发和维护软件应用程序，解决复杂的技术问题。",
                    salary: { min: 80000, max: 220000, currency: "USD" },
                    resources: [
                        { title: "LeetCode练习平台", url: "https://leetcode.com", type: "website" },
                        { title: "系统设计面试", url: "https://github.com/donnemartin/system-design-primer", type: "article" }
                    ],
                    job_examples: [
                        { title: "Senior Software Engineer", company: "Google", location: "Mountain View, CA", salary_range: "$150k-$250k" },
                        { title: "Full Stack Developer", company: "Meta", location: "Menlo Park, CA", salary_range: "$130k-$220k" }
                    ],
                    db_match_count: 523
                },
                {
                    title: "数据工程师",
                    description: "构建和维护数据管道，确保数据的质量、可用性和可扩展性。",
                    salary: { min: 90000, max: 200000, currency: "USD" },
                    resources: [
                        { title: "Apache Spark官方文档", url: "https://spark.apache.org/docs/latest/", type: "website" },
                        { title: "数据工程cookbook", url: "https://github.com/andkret/Cookbook", type: "article" }
                    ],
                    job_examples: [
                        { title: "Data Engineer", company: "Amazon", location: "Seattle, WA", salary_range: "$120k-$190k" },
                        { title: "Senior Data Engineer", company: "Uber", location: "San Francisco, CA", salary_range: "$140k-$210k" }
                    ],
                    db_match_count: 312
                },
                {
                    title: "DevOps工程师",
                    description: "管理软件开发和IT运维的自动化流程，确保系统的稳定性和可靠性。",
                    salary: { min: 85000, max: 180000, currency: "USD" },
                    resources: [
                        { title: "Kubernetes官方教程", url: "https://kubernetes.io/docs/tutorials/", type: "course" },
                        { title: "DevOps Handbook", url: "https://itrevolution.com/the-devops-handbook/", type: "book" }
                    ],
                    job_examples: [
                        { title: "DevOps Engineer", company: "Netflix", location: "Los Gatos, CA", salary_range: "$130k-$200k" },
                        { title: "Site Reliability Engineer", company: "Airbnb", location: "San Francisco, CA", salary_range: "$140k-$220k" }
                    ],
                    db_match_count: 287
                }
            ],
            "数据科学 (Data Science)": [
                {
                    title: "数据科学家",
                    description: "运用统计学、机器学习和编程技能，从数据中提取商业洞察和预测模型。",
                    salary: { min: 95000, max: 230000, currency: "USD" },
                    resources: [
                        { title: "Kaggle竞赛", url: "https://www.kaggle.com/competitions", type: "website" },
                        { title: "Hands-On Machine Learning", url: "https://www.oreilly.com/library/view/hands-on-machine-learning/9781492032632/", type: "book" }
                    ],
                    job_examples: [
                        { title: "Senior Data Scientist", company: "Microsoft", location: "Redmond, WA", salary_range: "$140k-$240k" },
                        { title: "Data Scientist", company: "Apple", location: "Cupertino, CA", salary_range: "$130k-$220k" }
                    ],
                    db_match_count: 445
                },
                {
                    title: "商业智能分析师",
                    description: "使用数据分析工具和技术为企业决策提供洞察和建议。",
                    salary: { min: 70000, max: 150000, currency: "USD" },
                    resources: [
                        { title: "Tableau教程", url: "https://www.tableau.com/learn/training", type: "course" },
                        { title: "SQL for Data Analysis", url: "https://mode.com/sql-tutorial/", type: "course" }
                    ],
                    job_examples: [
                        { title: "BI Analyst", company: "Salesforce", location: "San Francisco, CA", salary_range: "$90k-$140k" },
                        { title: "Senior Analytics Manager", company: "LinkedIn", location: "Sunnyvale, CA", salary_range: "$120k-$180k" }
                    ],
                    db_match_count: 198
                }
            ],
            "人工智能 (Artificial Intelligence)": [
                {
                    title: "机器学习工程师",
                    description: "设计和实现机器学习模型，将AI算法部署到生产环境。",
                    salary: { min: 100000, max: 250000, currency: "USD" },
                    resources: [
                        { title: "TensorFlow教程", url: "https://www.tensorflow.org/tutorials", type: "course" },
                        { title: "Machine Learning Yearning", url: "https://www.deeplearning.ai/machine-learning-yearning/", type: "book" }
                    ],
                    job_examples: [
                        { title: "ML Engineer", company: "OpenAI", location: "San Francisco, CA", salary_range: "$160k-$280k" },
                        { title: "Senior ML Engineer", company: "Tesla", location: "Palo Alto, CA", salary_range: "$150k-$260k" }
                    ],
                    db_match_count: 398
                },
                {
                    title: "AI研究科学家",
                    description: "开展前沿AI研究，发表学术论文，推动人工智能技术创新。",
                    salary: { min: 120000, max: 300000, currency: "USD" },
                    resources: [
                        { title: "arXiv AI论文", url: "https://arxiv.org/list/cs.AI/recent", type: "website" },
                        { title: "Deep Learning Book", url: "https://www.deeplearningbook.org/", type: "book" }
                    ],
                    job_examples: [
                        { title: "Research Scientist", company: "DeepMind", location: "London, UK", salary_range: "$150k-$320k" },
                        { title: "AI Research Lead", company: "Meta AI", location: "Menlo Park, CA", salary_range: "$180k-$350k" }
                    ],
                    db_match_count: 156
                }
            ]
        };
        
        return {
            success: true,
            careers: careersMap[majorName] || []
        };
    }
    
    /**
     * 显示加载动画
     */
    showLoading(step, message) {
        this.loadingOverlay.style.display = 'flex';
        
        const loadingTitle = document.getElementById('loadingTitle');
        const loadingText = document.getElementById('loadingText');
        
        if (step === 'major') {
            loadingTitle.textContent = 'AI is analyzing your career path...';
            loadingText.textContent = 'Major Research Agent is working';
        } else if (step === 'career') {
            loadingTitle.textContent = 'AI is analyzing career possibilities...';
            loadingText.textContent = 'Career Analysis Agent is working';
        }
        
        this.updateLoadingStep(step, 'active', message);
    }
    
    /**
     * 更新加载步骤状态
     */
    updateLoadingStep(step, status, message) {
        const stepElement = document.querySelector(`.step[data-step="${step}"]`);
        if (!stepElement) return;
        
        const textElement = stepElement.querySelector('.step-text');
        const statusElement = stepElement.querySelector('.step-status');
        
        if (status === 'active') {
            stepElement.classList.add('active');
            stepElement.classList.remove('complete');
            textElement.textContent = message || textElement.textContent;
            statusElement.textContent = '⏳';
        } else if (status === 'complete') {
            stepElement.classList.remove('active');
            stepElement.classList.add('complete');
            textElement.textContent = message || textElement.textContent;
            statusElement.textContent = '✅';
        }
    }
    
    /**
     * 隐藏加载动画
     */
    hideLoading() {
        this.loadingOverlay.style.display = 'none';
        
        // 重置步骤状态
        document.querySelectorAll('.step').forEach(step => {
            step.classList.remove('active', 'complete');
            step.querySelector('.step-status').textContent = '';
        });
    }
    
    /**
     * 显示错误消息
     */
    showError(message) {
        alert('Error: ' + message);  // 简单实现，可以改为更优雅的通知
    }
    
    /**
     * 重置查询
     */
    resetQuery() {
        this.currentQuery = null;
        this.majorsData = null;
        this.careersData = {};
        
        this.treeEngine.clear();
        this.treeSection.style.display = 'none';
        this.querySection.style.display = 'block';
        
        document.getElementById('userQuery').value = '';
    }
    
    /**
     * 导出数据
     */
    exportData() {
        const exportData = {
            query: this.currentQuery,
            majors: this.majorsData,
            careers: this.careersData,
            tree: this.treeEngine.exportData()
        };
        
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `career-planning-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    /**
     * 延迟函数
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    const app = new CareerPlanningApp();
    console.log('✅ AI Career Planning App initialized');
});

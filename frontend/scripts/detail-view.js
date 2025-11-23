/**
 * Detail View Manager
 * 
 * 管理模态框显示节点详细信息
 */

class DetailViewManager {
    constructor(modalId) {
        this.modal = document.getElementById(modalId);
        this.overlay = document.getElementById('modalOverlay');
        this.closeBtn = document.getElementById('modalClose');
        this.modalBody = document.getElementById('modalBody');
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // 关闭按钮
        this.closeBtn.addEventListener('click', () => this.hide());
        
        // 点击遮罩层关闭
        this.overlay.addEventListener('click', () => this.hide());
        
        // ESC键关闭
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.style.display === 'flex') {
                this.hide();
            }
        });
    }
    
    /**
     * 显示根节点详情
     */
    showRootDetails(node) {
        const content = `
            <div class="detail-header">
                <div class="detail-icon root-icon">🎯</div>
                <h2 class="detail-title">Your Career Exploration Query</h2>
            </div>
            <div class="detail-section">
                <h3>Query Content</h3>
                <p class="query-text">${this.escapeHtml(node.data.query)}</p>
            </div>
            <div class="detail-section">
                <h3>AI Analysis Status</h3>
                <p>✅ Major Research Agent has completed major research</p>
                <p>💡 Click on major nodes to view details and expand career paths</p>
            </div>
        `;
        
        this.modalBody.innerHTML = content;
        this.show();
    }
    
    /**
     * 显示Major节点详情
     */
    showMajorDetails(node) {
        const data = node.data;
        
        let content = `
            <div class="detail-header">
                <div class="detail-icon major-icon">📚</div>
                <h2 class="detail-title">${this.escapeHtml(data.name)}</h2>
            </div>
        `;
        
        // 描述 - 始终显示，即使为空
        content += `
            <div class="detail-section">
                <h3>Major Overview</h3>
                ${data.description ? 
                    `<p>${this.escapeHtml(data.description)}</p>` : 
                    `<p class="empty-hint">ℹ️ This major has no detailed description yet. Please check the learning resources below for more information.</p>`
                }
            </div>
        `;
        
        // 核心课程
        if (data.core_courses && data.core_courses.length > 0) {
            content += `
                <div class="detail-section">
                    <h3>Core Courses</h3>
                    <div class="tag-list">
                        ${data.core_courses.map(course => 
                            `<span class="tag">${this.escapeHtml(course)}</span>`
                        ).join('')}
                    </div>
                </div>
            `;
        }
        
        // 学习资源
        if (data.resources && data.resources.length > 0) {
            content += `
                <div class="detail-section">
                    <h3>Learning Resources</h3>
                    <div class="resource-list">
                        ${data.resources.map((resource, index) => {
                            // 兼容两种格式：字符串URL 或 {title, url, type} 对象
                            let url, title, type;
                            
                            if (typeof resource === 'string') {
                                url = resource;
                                // 从URL提取标题
                                try {
                                    const urlObj = new URL(resource);
                                    title = urlObj.hostname.replace('www.', '').replace('m.', '') + urlObj.pathname.split('/').filter(p => p).slice(0, 2).join('/');
                                    // 简化显示
                                    if (title.length > 50) {
                                        title = urlObj.hostname.replace('www.', '').replace('m.', '');
                                    }
                                } catch (e) {
                                    title = `资源 ${index + 1}`;
                                }
                                type = 'website';
                            } else {
                                url = resource.url || '#';
                                title = resource.title || `资源 ${index + 1}`;
                                type = resource.type || 'website';
                            }
                            
                            return `
                                <div class="resource-item">
                                    <a href="${url}" target="_blank" rel="noopener">
                                        ${this.getResourceIcon(type)}
                                        ${this.escapeHtml(title)}
                                    </a>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        }
        
        // 院校推荐
        if (data.universities && data.universities.length > 0) {
            content += `
                <div class="detail-section">
                    <h3>Recommended Universities</h3>
                    <div class="university-list">
                        ${data.universities.map(uni => `
                            <div class="university-item">
                                <strong>${this.escapeHtml(uni.name)}</strong>
                                ${uni.ranking ? `<span class="ranking">Rank #${uni.ranking}</span>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // 展开职业路径按钮
        if (!node.expanded) {
            content += `
                <div class="detail-section action-section">
                    <button class="btn-expand-careers" data-major-id="${node.id}" data-major-name="${this.escapeHtml(data.name)}">
                        <span class="btn-icon">💼</span>
                        <span class="btn-text">Expand Career Paths</span>
                        <span class="btn-hint">Call Career Analysis Agent</span>
                    </button>
                </div>
            `;
        } else {
            content += `
                <div class="detail-section action-hint">
                    <p>✅ <strong>Career paths expanded</strong> - View career nodes in the tree</p>
                </div>
            `;
        }
        
        this.modalBody.innerHTML = content;
        this.show();
    }
    
    /**
     * 显示Career节点详情
     */
    showCareerDetails(node) {
        const data = node.data;
        
        let content = `
            <div class="detail-header">
                <div class="detail-icon career-icon">💼</div>
                <h2 class="detail-title">${this.escapeHtml(data.title)}</h2>
            </div>
        `;
        
        // 职业描述 - 始终显示
        content += `
            <div class="detail-section">
                <h3>Career Overview</h3>
                ${data.description ? 
                    `<p>${this.escapeHtml(data.description)}</p>` : 
                    `<p class="empty-hint">ℹ️ This career has no detailed description yet. Please check the resources and job examples below for more information.</p>`
                }
            </div>
        `;
        
        // 薪资信息
        if (data.salary) {
            content += `
                <div class="detail-section">
                    <h3>💰 Salary Range</h3>
                    <div class="salary-info">
                        <div class="salary-range">
                            <span class="salary-label">Min:</span>
                            <span class="salary-value">${this.formatSalary(data.salary.min, data.salary.currency)}</span>
                        </div>
                        <div class="salary-range">
                            <span class="salary-label">Max:</span>
                            <span class="salary-value">${this.formatSalary(data.salary.max, data.salary.currency)}</span>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // 真实职位案例
        if (data.job_examples && data.job_examples.length > 0) {
            content += `
                <div class="detail-section">
                    <h3>🔍 Real Job Examples (from Database)</h3>
                    <div class="job-examples">
                        ${data.job_examples.map(job => `
                            <div class="job-card">
                                <h4>${this.escapeHtml(job.title)}</h4>
                                ${job.company ? `<p class="company">🏢 ${this.escapeHtml(job.company)}</p>` : ''}
                                ${job.location ? `<p class="location">📍 ${this.escapeHtml(job.location)}</p>` : ''}
                                ${job.salary_range ? `<p class="salary">💵 ${this.escapeHtml(job.salary_range)}</p>` : ''}
                            </div>
                        `).join('')}
                    </div>
                    ${data.db_match_count ? `<p class="match-info">✅ Matched from ${data.db_match_count} database positions</p>` : ''}
                </div>
            `;
        }
        
        // 学习资源
        if (data.resources && data.resources.length > 0) {
            content += `
                <div class="detail-section">
                    <h3>📖 Learning Resources</h3>
                    <div class="resource-list">
                        ${data.resources.map((resource, index) => {
                            // 兼容两种格式：字符串URL 或 {title, url, type} 对象
                            let url, title, type;
                            
                            if (typeof resource === 'string') {
                                url = resource;
                                // 从URL提取标题
                                try {
                                    const urlObj = new URL(resource);
                                    title = urlObj.hostname.replace('www.', '').replace('m.', '');
                                } catch (e) {
                                    title = `Resource ${index + 1}`;
                                }
                                type = 'website';
                            } else {
                                url = resource.url || '#';
                                title = resource.title || `Resource ${index + 1}`;
                                type = resource.type || 'website';
                            }
                            
                            return `
                                <div class="resource-item">
                                    <a href="${url}" target="_blank" rel="noopener">
                                        ${this.getResourceIcon(type)}
                                        ${this.escapeHtml(title)}
                                    </a>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        }
        
        this.modalBody.innerHTML = content;
        this.show();
    }
    
    /**
     * 格式化薪资
     */
    formatSalary(amount, currency = 'USD') {
        const symbols = { USD: '$', CNY: '¥', EUR: '€' };
        const symbol = symbols[currency] || currency;
        return `${symbol}${amount.toLocaleString()}`;
    }
    
    /**
     * 获取资源图标
     */
    getResourceIcon(type) {
        const icons = {
            video: '🎥',
            article: '📄',
            course: '🎓',
            book: '📚',
            website: '🌐'
        };
        return icons[type] || '🔗';
    }
    
    /**
     * HTML转义
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * 显示模态框
     */
    show() {
        this.modal.style.display = 'flex';
        // 触发重排以启用CSS动画
        this.modal.offsetHeight;
        this.modal.classList.add('active');
    }
    
    /**
     * 隐藏模态框
     */
    hide() {
        this.modal.classList.remove('active');
        setTimeout(() => {
            this.modal.style.display = 'none';
        }, 300);
    }
}

// Global instance
window.DetailViewManager = DetailViewManager;

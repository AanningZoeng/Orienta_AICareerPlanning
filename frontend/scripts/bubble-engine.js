/**
 * Bubble Tree Engine
 * 
 * 管理交互式泡泡树可视化的核心引擎
 * 支持动态节点扩展、力导向布局和平滑动画
 */

class BubbleTreeEngine {
    constructor(svgId) {
        this.svg = document.getElementById(svgId);
        
        // 确保获取实际容器宽度
        const container = this.svg.parentElement;
        this.width = container.clientWidth || window.innerWidth;
        this.height = 1100; // 增加高度以容纳四层节点
        
        this.svg.setAttribute('width', this.width);
        this.svg.setAttribute('height', this.height);
        
        this.nodesGroup = document.getElementById('nodesGroup');
        this.linksGroup = document.getElementById('linksGroup');
        
        // Tree data structure
        this.nodes = [];
        this.links = [];
        
        // Node type configurations - 增大节点以容纳完整文本
        this.nodeConfig = {
            root: { radius: 80, gradient: 'rootGradient', color: '#667eea' },
            major: { radius: 70, gradient: 'majorGradient', color: '#f093fb' },
            career: { radius: 60, gradient: 'careerGradient', color: '#4facfe' },
            future: { radius: 55, gradient: 'futureGradient', color: '#43e97b' }
        };
        
        // Layout settings - 使用实际宽度的中心
        this.centerX = this.width / 2;
        this.centerY = 150;
        
        // Layer Y positions - 每层固定高度
        this.layerY = {
            root: 150,
            major: 400,
            career: 650,
            future: 900
        };
        
        // Animation settings - 加快动画速度
        this.animationDuration = 400;
        
        // Tooltip element
        this.tooltip = null;
        this.createTooltip();
        
        // Event handlers
        this.onNodeClick = null;
        this.onNodeHover = null;
        
        // 监听窗口大小变化
        window.addEventListener('resize', () => this.handleResize());
    }
    
    /**
     * 创建tooltip元素
     */
    createTooltip() {
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'bubble-tooltip';
        this.tooltip.style.display = 'none';
        document.body.appendChild(this.tooltip);
        
        // 添加tooltip自身的悬停事件，保持显示
        this.tooltip.addEventListener('mouseenter', () => {
            // Tooltip保持显示
        });
        
        this.tooltip.addEventListener('mouseleave', () => {
            this.hideTooltip();
        });
    }
    
    /**
     * 显示tooltip
     */
    showTooltip(node, event) {
        if (!this.tooltip) return;
        
        let description = '';
        
        switch(node.type) {
            case 'root':
                description = 'Your career exploration query - click to see analysis status';
                break;
            case 'major':
                description = node.data.description || 'University major - click to view details and expand careers';
                // 限制30词
                description = this.truncateDescription(description, 30);
                break;
            case 'career':
                description = node.data.description || 'Career path - click to view salary, examples, and future progression';
                description = this.truncateDescription(description, 30);
                break;
            case 'future':
                description = 'Future career progression analysis - click to see 5-year statistics and paths';
                break;
        }
        
        this.tooltip.innerHTML = `
            <div class="tooltip-title">${this.escapeHtml(node.name)}</div>
            <div class="tooltip-desc">${this.escapeHtml(description)}</div>
        `;
        
        this.tooltip.style.display = 'block';
        this.tooltip.style.left = (event.pageX + 15) + 'px';
        this.tooltip.style.top = (event.pageY + 15) + 'px';
    }
    
    /**
     * 隐藏tooltip
     */
    hideTooltip() {
        if (this.tooltip) {
            this.tooltip.style.display = 'none';
        }
    }
    
    /**
     * 截断描述到指定词数
     */
    truncateDescription(text, maxWords) {
        const words = text.split(/\s+/);
        if (words.length <= maxWords) return text;
        return words.slice(0, maxWords).join(' ') + '...';
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
     * 处理窗口大小变化
     */
    handleResize() {
        const container = this.svg.parentElement;
        const newWidth = container.clientWidth || window.innerWidth;
        
        if (Math.abs(newWidth - this.width) > 50) {
            this.width = newWidth;
            this.svg.setAttribute('width', this.width);
            this.centerX = this.width / 2;
            
            // 重新计算所有节点位置
            this.recalculatePositions();
            this.render();
        }
    }
    
    /**
     * 重新计算节点位置
     */
    recalculatePositions() {
        // 更新根节点
        const rootNode = this.nodes.find(n => n.type === 'root');
        if (rootNode) {
            rootNode.x = this.centerX;
        }
        
        // 更新major节点
        const majorNodes = this.nodes.filter(n => n.type === 'major');
        const majorCount = majorNodes.length;
        if (majorCount > 0) {
            const angleStep = (2 * Math.PI) / majorCount;
            const radius = 250;
            
            majorNodes.forEach((node, index) => {
                const angle = angleStep * index - Math.PI / 2;
                const x = this.centerX + radius * Math.cos(angle);
                node.x = x;
                if (node.targetX !== undefined) {
                    node.targetX = x;
                }
            });
        }
    }
    
    /**
     * 初始化树 - 创建根节点
     */
    initializeTree(userQuery) {
        this.clear();
        
        const rootNode = {
            id: 'root',
            type: 'root',
            name: userQuery,
            x: this.centerX,
            y: this.centerY,
            children: [],
            data: { query: userQuery }
        };
        
        this.nodes.push(rootNode);
        this.render();
        return rootNode;
    }
    
    /**
     * 添加Major节点
     */
    addMajors(majors) {
        const rootNode = this.nodes.find(n => n.type === 'root');
        if (!rootNode) return;
        
        const majorCount = majors.length;
        const y = this.layerY.major; // 固定在major层
        
        // 计算水平分布
        const totalWidth = this.width * 0.8; // 使用80%的宽度
        const spacing = totalWidth / (majorCount + 1);
        const startX = (this.width - totalWidth) / 2;
        
        majors.forEach((major, index) => {
            const x = startX + spacing * (index + 1);
            
            const majorNode = {
                id: `major-${index}`,
                type: 'major',
                name: major.name,
                x: this.centerX,  // Start from center for animation
                y: this.centerY,
                targetX: x,
                targetY: y,
                children: [],
                expanded: false,
                data: major
            };
            
            this.nodes.push(majorNode);
            this.links.push({
                source: rootNode.id,
                target: majorNode.id
            });
            
            rootNode.children.push(majorNode.id);
        });
        
        this.animateNodes();
    }
    
    /**
     * 展开Major节点 - 添加Career子节点
     */
    expandMajor(majorId, careers) {
        const majorNode = this.nodes.find(n => n.id === majorId);
        if (!majorNode || majorNode.expanded) return;
        
        majorNode.expanded = true;
        
        const parentX = majorNode.x;
        const parentY = majorNode.y;
        const y = this.layerY.career; // 固定在career层
        
        const careerCount = careers.length;
        
        // 计算career节点的水平分布，围绕父节点
        const spreadWidth = Math.min(300 * careerCount, this.width * 0.4);
        const spacing = spreadWidth / (careerCount + 1);
        const startX = parentX - spreadWidth / 2;
        
        careers.forEach((career, index) => {
            const x = startX + spacing * (index + 1);
            
            const careerId = `${majorId}-career-${index}`;
            const careerNode = {
                id: careerId,
                type: 'career',
                name: career.title,
                x: parentX,  // Start from parent for animation
                y: parentY,
                targetX: x,
                targetY: y,
                data: career,
                parent: majorId,
                children: []
            };
            
            this.nodes.push(careerNode);
            this.links.push({
                source: majorId,
                target: careerId
            });
            
            majorNode.children.push(careerId);
        });
        
        // 先渲染连线，再执行动画
        this.render();
        this.animateNodes();
    }
    
    /**
     * 展开Career节点 - 添加Future Path子节点
     */
    expandCareer(careerId, futurePath) {
        const careerNode = this.nodes.find(n => n.id === careerId);
        if (!careerNode || careerNode.expanded) return;
        
        careerNode.expanded = true;
        
        const parentX = careerNode.x;
        const parentY = careerNode.y;
        const y = this.layerY.future; // 固定在future层
        
        // Future path节点直接在父节点下方
        const x = parentX;
        
        const futureId = `${careerId}-future`;
        const futureNode = {
            id: futureId,
            type: 'future',
            name: 'Future Path',
            x: parentX,  // Start from parent for animation
            y: parentY,
            targetX: x,
            targetY: y,
            data: futurePath,
            parent: careerId
        };
        
        this.nodes.push(futureNode);
        this.links.push({
            source: careerId,
            target: futureId
        });
        
        careerNode.children = careerNode.children || [];
        careerNode.children.push(futureId);
        
        // 先渲染连线，再执行动画
        this.render();
        this.animateNodes();
    }
    
    /**
     * 渲染树结构
     */
    render() {
        this.renderLinks();
        this.renderNodes();
    }
    
    /**
     * 渲染连接线
     */
    renderLinks() {
        this.linksGroup.innerHTML = '';
        
        this.links.forEach(link => {
            const sourceNode = this.nodes.find(n => n.id === link.source);
            const targetNode = this.nodes.find(n => n.id === link.target);
            
            if (sourceNode && targetNode) {
                const line = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                
                // 优化的曲线路径，适应层次布局
                const sourceY = sourceNode.y + this.nodeConfig[sourceNode.type].radius;
                const targetY = targetNode.y - this.nodeConfig[targetNode.type].radius;
                
                // 控制点在中间偏下
                const controlY = sourceY + (targetY - sourceY) * 0.5;
                
                const d = `M ${sourceNode.x} ${sourceY} 
                           C ${sourceNode.x} ${controlY}, 
                             ${targetNode.x} ${controlY}, 
                             ${targetNode.x} ${targetY}`;
                
                line.setAttribute('d', d);
                line.setAttribute('class', 'tree-link');
                line.setAttribute('data-source', link.source);
                line.setAttribute('data-target', link.target);
                
                // 根据节点类型设置连线颜色
                if (targetNode.type === 'major') {
                    line.setAttribute('stroke', 'rgba(240, 147, 251, 0.4)');
                } else if (targetNode.type === 'career') {
                    line.setAttribute('stroke', 'rgba(79, 172, 254, 0.4)');
                } else if (targetNode.type === 'future') {
                    line.setAttribute('stroke', 'rgba(67, 233, 123, 0.4)');
                }
                
                this.linksGroup.appendChild(line);
            }
        });
    }
    
    /**
     * 渲染节点
     */
    renderNodes() {
        this.nodesGroup.innerHTML = '';
        
        this.nodes.forEach(node => {
            const config = this.nodeConfig[node.type];
            
            // 创建节点组
            const nodeGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            nodeGroup.setAttribute('class', `tree-node ${node.type}-node`);
            nodeGroup.setAttribute('data-id', node.id);
            nodeGroup.setAttribute('transform', `translate(${node.x}, ${node.y})`);
            
            // 主圆圈
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('r', config.radius);
            circle.setAttribute('fill', `url(#${config.gradient})`);
            circle.setAttribute('filter', 'url(#dropShadow)');
            circle.setAttribute('class', 'node-circle');
            
            // 添加点击和悬停事件
            nodeGroup.style.cursor = 'pointer';
            nodeGroup.addEventListener('click', (e) => {
                e.stopPropagation();
                if (this.onNodeClick) {
                    this.onNodeClick(node);
                }
            });
            
            nodeGroup.addEventListener('mouseenter', (e) => {
                circle.setAttribute('filter', 'url(#glow)');
                this.showTooltip(node, e);
                if (this.onNodeHover) {
                    this.onNodeHover(node);
                }
            });
            
            nodeGroup.addEventListener('mouseleave', (e) => {
                circle.setAttribute('filter', 'url(#dropShadow)');
                // 检查是否移动到tooltip上
                const relatedTarget = e.relatedTarget;
                if (!this.tooltip || !this.tooltip.contains(relatedTarget)) {
                    this.hideTooltip();
                }
            });
            
            nodeGroup.addEventListener('mousemove', (e) => {
                if (this.tooltip && this.tooltip.style.display === 'block') {
                    this.tooltip.style.left = (e.pageX + 15) + 'px';
                    this.tooltip.style.top = (e.pageY + 15) + 'px';
                }
            });
            
            nodeGroup.appendChild(circle);
            
            // 文本标签 - 显示完整名称
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('class', 'node-label');
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('dy', '0.35em');
            text.setAttribute('fill', 'white');
            text.setAttribute('font-size', node.type === 'root' ? '15' : (node.type === 'future' ? '13' : '14'));
            text.setAttribute('font-weight', node.type === 'root' ? 'bold' : '600');
            
            // 处理长文本，自动换行
            const maxWidth = config.radius * 1.8;
            this.wrapText(text, node.name, maxWidth);
            
            nodeGroup.appendChild(text);
            
            // 扩展状态指示器 (for majors and careers)
            if (node.type === 'major' || node.type === 'career') {
                const indicator = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                indicator.setAttribute('r', '10');
                indicator.setAttribute('cx', config.radius - 10);
                indicator.setAttribute('cy', -config.radius + 10);
                indicator.setAttribute('fill', node.expanded ? '#4ade80' : '#fbbf24');
                indicator.setAttribute('class', 'expand-indicator');
                indicator.setAttribute('stroke', '#fff');
                indicator.setAttribute('stroke-width', '2');
                
                const icon = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                icon.setAttribute('x', config.radius - 10);
                icon.setAttribute('y', -config.radius + 10);
                icon.setAttribute('text-anchor', 'middle');
                icon.setAttribute('dy', '0.35em');
                icon.setAttribute('fill', '#fff');
                icon.setAttribute('font-size', '14');
                icon.setAttribute('font-weight', 'bold');
                icon.textContent = node.expanded ? '✓' : '+';
                
                nodeGroup.appendChild(indicator);
                nodeGroup.appendChild(icon);
            }
            
            this.nodesGroup.appendChild(nodeGroup);
        });
    }
    
    /**
     * 动画更新节点位置
     */
    animateNodes() {
        const nodesToAnimate = this.nodes.filter(n => n.targetX !== undefined);
        
        if (nodesToAnimate.length === 0) {
            this.render();
            return;
        }
        
        const startTime = Date.now();
        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / this.animationDuration, 1);
            
            // Easing function (easeOutCubic)
            const eased = 1 - Math.pow(1 - progress, 3);
            
            nodesToAnimate.forEach(node => {
                const startX = node.x;
                const startY = node.y;
                node.x = startX + (node.targetX - startX) * eased;
                node.y = startY + (node.targetY - startY) * eased;
            });
            
            this.render();
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                // 完成动画后清理target属性
                nodesToAnimate.forEach(node => {
                    node.x = node.targetX;
                    node.y = node.targetY;
                    delete node.targetX;
                    delete node.targetY;
                });
            }
        };
        
        requestAnimationFrame(animate);
    }
    
    /**
     * 文本换行处理
     */
    wrapText(textElement, text, maxWidth) {
        const words = text.split(/\s+/);
        const fontSize = parseFloat(textElement.getAttribute('font-size'));
        const lineHeight = fontSize * 1.2;
        
        let lines = [];
        let currentLine = '';
        
        // 简单估算每个单词的宽度
        words.forEach(word => {
            const testLine = currentLine ? currentLine + ' ' + word : word;
            const estimatedWidth = testLine.length * fontSize * 0.6; // 粗略估算
            
            if (estimatedWidth > maxWidth && currentLine) {
                lines.push(currentLine);
                currentLine = word;
            } else {
                currentLine = testLine;
            }
        });
        
        if (currentLine) {
            lines.push(currentLine);
        }
        
        // 限制最多3行
        if (lines.length > 3) {
            lines = lines.slice(0, 3);
            lines[2] = lines[2].substring(0, 15) + '...';
        }
        
        // 计算起始Y位置，使文本居中
        const startY = -(lines.length - 1) * lineHeight / 2;
        
        // 添加每一行
        lines.forEach((line, i) => {
            const tspan = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
            tspan.setAttribute('x', '0');
            tspan.setAttribute('dy', i === 0 ? startY : lineHeight);
            tspan.textContent = line;
            textElement.appendChild(tspan);
        });
    }
    
    /**
     * 截断文本以适应节点（已被wrapText替代）
     */
    truncateText(text, radius) {
        const maxLength = Math.floor(radius / 4);
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength - 2) + '...';
    }
    
    /**
     * 清除树
     */
    clear() {
        this.nodes = [];
        this.links = [];
        this.nodesGroup.innerHTML = '';
        this.linksGroup.innerHTML = '';
    }
    
    /**
     * 获取节点数据
     */
    getNode(nodeId) {
        return this.nodes.find(n => n.id === nodeId);
    }
    
    /**
     * 导出树数据
     */
    exportData() {
        return {
            nodes: this.nodes.map(n => ({
                id: n.id,
                type: n.type,
                name: n.name,
                data: n.data
            })),
            links: this.links
        };
    }
}

// Global instance
window.BubbleTreeEngine = BubbleTreeEngine;

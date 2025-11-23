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
        this.height = 900;
        
        this.svg.setAttribute('width', this.width);
        this.svg.setAttribute('height', this.height);
        
        this.nodesGroup = document.getElementById('nodesGroup');
        this.linksGroup = document.getElementById('linksGroup');
        
        // Tree data structure
        this.nodes = [];
        this.links = [];
        
        // Node type configurations
        this.nodeConfig = {
            root: { radius: 60, gradient: 'rootGradient', color: '#667eea' },
            major: { radius: 50, gradient: 'majorGradient', color: '#f093fb' },
            career: { radius: 40, gradient: 'careerGradient', color: '#4facfe' },
            future: { radius: 35, gradient: 'futureGradient', color: '#43e97b' }
        };
        
        // Layout settings - 使用实际宽度的中心
        this.centerX = this.width / 2;
        this.centerY = 200;
        this.levelSpacing = 280;
        
        // Animation settings
        this.animationDuration = 600;
        
        // Event handlers
        this.onNodeClick = null;
        this.onNodeHover = null;
        
        // 监听窗口大小变化
        window.addEventListener('resize', () => this.handleResize());
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
        const angleStep = (2 * Math.PI) / majorCount;
        const radius = 250;
        
        majors.forEach((major, index) => {
            const angle = angleStep * index - Math.PI / 2;
            const x = this.centerX + radius * Math.cos(angle);
            const y = this.centerY + this.levelSpacing + radius * Math.sin(angle) * 0.3;
            
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
        
        // 使用majorNode的当前位置(x, y)而不是targetX/targetY
        const parentX = majorNode.x;
        const parentY = majorNode.y;
        
        const careerCount = careers.length;
        const angleStep = (Math.PI * 1.2) / Math.max(careerCount - 1, 1);
        const startAngle = -Math.PI / 3;
        const radius = 180;
        
        careers.forEach((career, index) => {
            const angle = startAngle + angleStep * index;
            const x = parentX + radius * Math.cos(angle);
            const y = parentY + radius * Math.sin(angle) + 120;
            
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
                parent: majorId
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
        
        // 使用careerNode的当前位置
        const parentX = careerNode.x;
        const parentY = careerNode.y;
        
        // Future path只有一个节点，放在career下方
        const radius = 150;
        const x = parentX;
        const y = parentY + radius;
        
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
                
                // 曲线路径 (三次贝塞尔曲线)
                const midY = (sourceNode.y + targetNode.y) / 2;
                const d = `M ${sourceNode.x} ${sourceNode.y} 
                           C ${sourceNode.x} ${midY}, 
                             ${targetNode.x} ${midY}, 
                             ${targetNode.x} ${targetNode.y}`;
                
                line.setAttribute('d', d);
                line.setAttribute('class', 'tree-link');
                line.setAttribute('data-source', link.source);
                line.setAttribute('data-target', link.target);
                
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
            
            nodeGroup.addEventListener('mouseenter', () => {
                circle.setAttribute('filter', 'url(#glow)');
                if (this.onNodeHover) {
                    this.onNodeHover(node);
                }
            });
            
            nodeGroup.addEventListener('mouseleave', () => {
                circle.setAttribute('filter', 'url(#dropShadow)');
            });
            
            nodeGroup.appendChild(circle);
            
            // 文本标签
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('class', 'node-label');
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('dy', '0.35em');
            text.setAttribute('fill', 'white');
            text.setAttribute('font-size', node.type === 'root' ? '16' : '14');
            text.setAttribute('font-weight', node.type === 'root' ? 'bold' : '500');
            text.textContent = this.truncateText(node.name, config.radius);
            
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
     * 截断文本以适应节点
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

/**
 * Tree Visualization Engine
 * Renders an interactive career path tree with SVG
 */

class TreeEngine {
    constructor(svgId) {
        this.svg = document.getElementById(svgId);
        this.nodesGroup = document.getElementById('nodesGroup');
        this.linksGroup = document.getElementById('linksGroup');
        
        // Tree data structure
        this.rootNode = null;
        this.nodes = [];
        this.links = [];
        
        // Layout parameters
        this.nodeRadius = {
            root: 80,
            major: 65,
            career: 55,
            future: 50
        };
        
        this.levelSpacing = 250;  // Vertical spacing between levels
        this.siblingSpacing = 180;  // Horizontal spacing between siblings
        
        // Animation state
        this.isAnimating = false;
        
        // Callbacks
        this.onNodeClick = null;
        this.onNodeHover = null;
        
        this.setupEventListeners();
    }
    
    /**
     * Initialize the tree with a root node (user input)
     */
    initializeTree(userQuery) {
        this.clear();
        
        // Create root node
        this.rootNode = {
            id: 'root',
            type: 'root',
            label: 'Your Career Path',
            userQuery: userQuery,
            x: this.svg.clientWidth / 2,
            y: 100,
            children: [],
            expanded: false,
            data: { userQuery }
        };
        
        this.nodes = [this.rootNode];
        this.render();
        
        // Make root node editable (show input form in modal)
        this.showRootInput();
    }
    
    /**
     * Show root node input form
     */
    showRootInput() {
        const modal = document.getElementById('detailModal');
        const modalBody = document.getElementById('modalBody');
        
        modalBody.innerHTML = `
            <h2>Tell us about your interests</h2>
            <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">
                Describe your passions, skills, and career goals. Our AI will analyze and recommend personalized paths.
            </p>
            <form id="rootInputForm">
                <textarea 
                    id="rootQueryInput" 
                    placeholder="e.g., I love technology and solving problems. I'm interested in AI and want to make a positive impact..."
                    rows="5"
                    required
                    style="width: 100%; padding: 1rem; border-radius: 8px; border: 2px solid var(--border-color); background: var(--bg-darker); color: var(--text-primary); font-family: inherit; font-size: 1rem; margin-bottom: 1rem;"
                ></textarea>
                <button type="submit" class="btn-primary" style="width: 100%;">
                    <span>✨</span>
                    <span>Generate My Career Path</span>
                </button>
            </form>
        `;
        
        modal.style.display = 'flex';
        
        // Handle form submission
        document.getElementById('rootInputForm').addEventListener('submit', (e) => {
            e.preventDefault();
            const query = document.getElementById('rootQueryInput').value.trim();
            if (query) {
                this.rootNode.userQuery = query;
                this.rootNode.data.userQuery = query;
                modal.style.display = 'none';
                
                // Trigger callback to fetch majors
                if (this.onNodeClick) {
                    this.onNodeClick(this.rootNode, 'expand');
                }
            }
        });
    }
    
    /**
     * Add major nodes as children of root
     */
    addMajors(majorsData) {
        if (!this.rootNode) return;
        
        // Clear existing children
        this.rootNode.children = [];
        
        // Convert majorsData object to array
        const majorsList = Object.entries(majorsData).map(([name, data]) => ({
            name,
            ...data
        }));
        
        // Create major nodes
        majorsList.forEach((major, index) => {
            const majorNode = {
                id: `major-${index}`,
                type: 'major',
                label: major.name,
                parent: this.rootNode,
                children: [],
                expanded: false,
                data: major
            };
            
            this.rootNode.children.push(majorNode);
            this.nodes.push(majorNode);
        });
        
        this.rootNode.expanded = true;
        this.calculateLayout();
        this.render();
    }
    
    /**
     * Add career nodes as children of a major node
     */
    addCareers(majorNodeId, careersData) {
        const majorNode = this.nodes.find(n => n.id === majorNodeId);
        if (!majorNode) return;
        
        // Clear existing children
        majorNode.children = [];
        
        // Convert careersData object to array
        const careersList = Object.entries(careersData).map(([title, data]) => ({
            title,
            ...data
        }));
        
        // Create career nodes
        careersList.forEach((career, index) => {
            const careerNode = {
                id: `${majorNodeId}-career-${index}`,
                type: 'career',
                label: career.title,
                parent: majorNode,
                children: [],
                expanded: false,
                data: career
            };
            
            majorNode.children.push(careerNode);
            this.nodes.push(careerNode);
        });
        
        majorNode.expanded = true;
        this.calculateLayout();
        this.render();
    }
    
    /**
     * Add future path nodes as children of a career node
     */
    addFuturePaths(careerNodeId, futurePathsData) {
        const careerNode = this.nodes.find(n => n.id === careerNodeId);
        if (!careerNode) return;
        
        // Clear existing children
        careerNode.children = [];
        
        // Create future path nodes (mock data structure)
        const futuresList = Array.isArray(futurePathsData) ? futurePathsData : 
            ['5 Year Outlook', '10 Year Outlook', 'Long-term Growth'];
        
        futuresList.forEach((future, index) => {
            const futureNode = {
                id: `${careerNodeId}-future-${index}`,
                type: 'future',
                label: typeof future === 'string' ? future : future.title || `Path ${index + 1}`,
                parent: careerNode,
                children: [],
                expanded: false,
                data: typeof future === 'object' ? future : { title: future }
            };
            
            careerNode.children.push(futureNode);
            this.nodes.push(futureNode);
        });
        
        careerNode.expanded = true;
        this.calculateLayout();
        this.render();
    }
    
    /**
     * Calculate node positions using tree layout algorithm
     */
    calculateLayout() {
        if (!this.rootNode) return;
        
        // Use a simple tree layout: BFS to assign levels and positions
        const levels = [];
        const queue = [{node: this.rootNode, level: 0}];
        
        while (queue.length > 0) {
            const {node, level} = queue.shift();
            
            if (!levels[level]) {
                levels[level] = [];
            }
            levels[level].push(node);
            
            if (node.expanded && node.children) {
                node.children.forEach(child => {
                    queue.push({node: child, level: level + 1});
                });
            }
        }
        
        // Calculate positions for each level
        const svgWidth = this.svg.clientWidth;
        const startY = 100;
        
        levels.forEach((levelNodes, levelIndex) => {
            const y = startY + levelIndex * this.levelSpacing;
            const totalWidth = (levelNodes.length - 1) * this.siblingSpacing;
            const startX = (svgWidth - totalWidth) / 2;
            
            levelNodes.forEach((node, nodeIndex) => {
                node.x = startX + nodeIndex * this.siblingSpacing;
                node.y = y;
            });
        });
        
        // Calculate links
        this.links = [];
        this.nodes.forEach(node => {
            if (node.parent) {
                this.links.push({
                    source: node.parent,
                    target: node
                });
            }
        });
    }
    
    /**
     * Render the tree
     */
    render() {
        this.renderLinks();
        this.renderNodes();
    }
    
    /**
     * Render links (edges) between nodes
     */
    renderLinks() {
        this.linksGroup.innerHTML = '';
        
        this.links.forEach(link => {
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            
            // Create curved path
            const sourceX = link.source.x;
            const sourceY = link.source.y + this.nodeRadius[link.source.type];
            const targetX = link.target.x;
            const targetY = link.target.y - this.nodeRadius[link.target.type];
            
            const midY = (sourceY + targetY) / 2;
            
            const pathData = `M ${sourceX} ${sourceY} 
                             C ${sourceX} ${midY}, 
                               ${targetX} ${midY}, 
                               ${targetX} ${targetY}`;
            
            path.setAttribute('d', pathData);
            path.setAttribute('stroke', 'hsla(240, 30%, 50%, 0.3)');
            path.setAttribute('stroke-width', '2');
            path.setAttribute('fill', 'none');
            path.setAttribute('class', 'tree-link');
            
            this.linksGroup.appendChild(path);
        });
    }
    
    /**
     * Render nodes (circles with labels)
     */
    renderNodes() {
        this.nodesGroup.innerHTML = '';
        
        this.nodes.forEach(node => {
            const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            group.setAttribute('class', `tree-node tree-node-${node.type}`);
            group.setAttribute('data-node-id', node.id);
            group.setAttribute('transform', `translate(${node.x}, ${node.y})`);
            
            // Circle
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('r', this.nodeRadius[node.type]);
            circle.setAttribute('fill', `url(#${node.type}Gradient)`);
            circle.setAttribute('filter', 'url(#dropShadow)');
            circle.setAttribute('class', 'node-circle');
            
            // Label (text wrapped)
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('dominant-baseline', 'middle');
            text.setAttribute('fill', 'white');
            text.setAttribute('font-size', node.type === 'root' ? '16' : '14');
            text.setAttribute('font-weight', '600');
            text.setAttribute('class', 'node-text');
            
            // Wrap text if too long
            const words = node.label.split(' ');
            const maxCharsPerLine = node.type === 'root' ? 12 : 10;
            let lines = [];
            let currentLine = '';
            
            words.forEach(word => {
                if ((currentLine + word).length > maxCharsPerLine && currentLine.length > 0) {
                    lines.push(currentLine.trim());
                    currentLine = word + ' ';
                } else {
                    currentLine += word + ' ';
                }
            });
            if (currentLine.trim()) {
                lines.push(currentLine.trim());
            }
            
            // Limit to 3 lines
            lines = lines.slice(0, 3);
            if (lines.length === 1) {
                text.textContent = lines[0];
            } else {
                lines.forEach((line, i) => {
                    const tspan = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
                    tspan.setAttribute('x', '0');
                    tspan.setAttribute('dy', i === 0 ? `-${(lines.length - 1) * 0.6}em` : '1.2em');
                    tspan.textContent = line;
                    text.appendChild(tspan);
                });
            }
            
            // Expansion indicator (if node has/can have children)
            if (node.type !== 'future') {
                const indicator = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                indicator.setAttribute('cx', '0');
                indicator.setAttribute('cy', this.nodeRadius[node.type] + 15);
                indicator.setAttribute('r', '8');
                indicator.setAttribute('fill', node.expanded ? 'hsla(120, 60%, 50%, 0.8)' : 'hsla(0, 0%, 70%, 0.6)');
                indicator.setAttribute('class', 'expansion-indicator');
                
                const indicatorText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                indicatorText.setAttribute('x', '0');
                indicatorText.setAttribute('y', this.nodeRadius[node.type] + 15);
                indicatorText.setAttribute('text-anchor', 'middle');
                indicatorText.setAttribute('dominant-baseline', 'middle');
                indicatorText.setAttribute('fill', 'white');
                indicatorText.setAttribute('font-size', '10');
                indicatorText.setAttribute('font-weight', 'bold');
                indicatorText.textContent = node.expanded ? '−' : '+';
                
                group.appendChild(indicator);
                group.appendChild(indicatorText);
            }
            
            group.appendChild(circle);
            group.appendChild(text);
            
            this.nodesGroup.appendChild(group);
        });
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Click event
        this.svg.addEventListener('click', (e) => {
            const nodeGroup = e.target.closest('.tree-node');
            if (nodeGroup) {
                const nodeId = nodeGroup.getAttribute('data-node-id');
                const node = this.nodes.find(n => n.id === nodeId);
                if (node && this.onNodeClick) {
                    this.onNodeClick(node);
                }
            }
        });
        
        // Hover event
        this.svg.addEventListener('mouseover', (e) => {
            const nodeGroup = e.target.closest('.tree-node');
            if (nodeGroup) {
                nodeGroup.style.cursor = 'pointer';
                const circle = nodeGroup.querySelector('.node-circle');
                circle.style.filter = 'url(#dropShadow) brightness(1.2)';
            }
        });
        
        this.svg.addEventListener('mouseout', (e) => {
            const nodeGroup = e.target.closest('.tree-node');
            if (nodeGroup) {
                const circle = nodeGroup.querySelector('.node-circle');
                circle.style.filter = 'url(#dropShadow)';
            }
        });
        
        // Close modal
        document.getElementById('modalClose').addEventListener('click', () => {
            document.getElementById('detailModal').style.display = 'none';
        });
        
        document.getElementById('modalOverlay').addEventListener('click', () => {
            document.getElementById('detailModal').style.display = 'none';
        });
    }
    
    /**
     * Show node details in modal
     */
    showNodeDetails(node) {
        const modal = document.getElementById('detailModal');
        const modalTitle = document.getElementById('modalTitle');
        const modalDescription = document.getElementById('modalDescription');
        const modalResources = document.getElementById('modalResources');
        
        modalTitle.textContent = node.label;
        
        // Description
        if (node.data.description) {
            modalDescription.innerHTML = `
                <h3>Description</h3>
                <p>${node.data.description}</p>
            `;
        } else if (node.data.userQuery) {
            modalDescription.innerHTML = `
                <h3>Your Input</h3>
                <p>${node.data.userQuery}</p>
            `;
        } else {
            modalDescription.innerHTML = '';
        }
        
        // Resources
        if (node.data.resources && node.data.resources.length > 0) {
            const resourcesHtml = node.data.resources.map((url, i) => 
                `<li><a href="${url}" target="_blank" rel="noopener">${url}</a></li>`
            ).join('');
            
            modalResources.innerHTML = `
                <h3>Resources</h3>
                <ul style="list-style: none; padding: 0;">
                    ${resourcesHtml}
                </ul>
            `;
        } else {
            modalResources.innerHTML = '';
        }
        
        modal.style.display = 'flex';
    }
    
    /**
     * Clear the tree
     */
    clear() {
        this.rootNode = null;
        this.nodes = [];
        this.links = [];
        this.nodesGroup.innerHTML = '';
        this.linksGroup.innerHTML = '';
    }
}

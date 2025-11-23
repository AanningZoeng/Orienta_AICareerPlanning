/**
 * Bubble Engine - Manages bubble visualization and interactions
 * Creates interactive, animated bubbles on canvas with physics-based positioning
 */

class BubbleEngine {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error('[BubbleEngine] Canvas element not found!');
            return;
        }
        this.ctx = this.canvas.getContext('2d');
        this.bubbles = [];
        this.currentLayer = 'majors'; // 'majors', 'careers', 'futures'
        this.selectedMajor = null;
        this.selectedCareer = null;
        this.hoveredBubble = null;
        this.isRendering = false;

        console.log('[BubbleEngine] Initializing...');

        // Setup canvas
        this.setupCanvas();

        console.log('[BubbleEngine] Canvas setup complete:', this.canvas.width, 'x', this.canvas.height);

        // Bind events
        this.canvas.addEventListener('click', this.handleClick.bind(this));
        this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
        window.addEventListener('resize', this.setupCanvas.bind(this));
    }

    setupCanvas() {
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;

        if (this.bubbles.length > 0) {
            this.render();
        }
    }

    /**
     * Display bubbles for majors
     */
    showMajors(majors) {
        console.log('[BubbleEngine] showMajors called with', majors.length, 'majors');
        console.log('[BubbleEngine] Canvas dimensions:', this.canvas.width, 'x', this.canvas.height);
        this.currentLayer = 'majors';
        this.selectedMajor = null;
        this.selectedCareer = null;
        this.bubbles = this.createBubbles(majors, 'major');
        console.log('[BubbleEngine] Created', this.bubbles.length, 'bubbles');
        if (this.bubbles.length > 0) {
            console.log('[BubbleEngine] First bubble:', this.bubbles[0]);
        }
        this.startRender();
    }

    /**
     * Display bubbles for careers (when a major is clicked)
     */
    showCareers(careers, majorName) {
        this.currentLayer = 'careers';
        this.selectedCareer = null;
        this.bubbles = this.createBubbles(careers, 'career');
        this.startRender();
    }

    /**
     * Display bubbles for future paths (when a career is clicked)
     */
    showFutures(futures, careerName) {
        this.currentLayer = 'futures';
        this.bubbles = this.createBubbles(futures, 'future');
        this.startRender();
    }

    /**
     * Create bubble objects from data
     */
    createBubbles(items, type) {
        const bubbles = [];
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const count = items.length;

        items.forEach((item, index) => {
            // Calculate size based on type
            let radius;
            if (type === 'major') {
                radius = 60 + Math.random() * 20; // 60-80px
            } else if (type === 'career') {
                radius = 50 + Math.random() * 15; // 50-65px
            } else {
                radius = 45 + Math.random() * 10; // 45-55px
            }

            // Calculate position in a circle around center
            const angle = (index / count) * Math.PI * 2;
            const distance = Math.min(centerX, centerY) * 0.5;

            const bubble = {
                id: item.id,
                name: item.name || item.title || item.career,
                type: type,
                data: item,
                x: centerX + Math.cos(angle) * distance,
                y: centerY + Math.sin(angle) * distance,
                radius: radius,
                targetX: centerX + Math.cos(angle) * distance,
                targetY: centerY + Math.sin(angle) * distance,
                vx: 0,
                vy: 0
            };

            bubbles.push(bubble);
        });

        return bubbles;
    }

    /**
     * Start the render loop
     */
    startRender() {
        if (!this.isRendering) {
            console.log('[BubbleEngine] Starting render loop');
            this.isRendering = true;
            this.render();
        }
    }

    /**
     * Render all bubbles with animations
     */
    render() {
        if (!this.isRendering) return;

        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Update bubble positions (simple physics)
        this.bubbles.forEach(bubble => {
            // Move towards target position
            const dx = bubble.targetX - bubble.x;
            const dy = bubble.targetY - bubble.y;
            bubble.vx += dx * 0.1;
            bubble.vy += dy * 0.1;

            // Apply friction
            bubble.vx *= 0.8;
            bubble.vy *= 0.8;

            bubble.x += bubble.vx;
            bubble.y += bubble.vy;
        });

        // Draw bubbles
        this.bubbles.forEach(bubble => {
            this.drawBubble(bubble);
        });

        // Continue animation
        requestAnimationFrame(() => this.render());
    }

    /**
     * Draw a single bubble
     */
    drawBubble(bubble) {
        const isHovered = this.hoveredBubble === bubble;
        const radius = isHovered ? bubble.radius * 1.15 : bubble.radius;

        // Create gradient based on type
        let gradient;
        if (bubble.type === 'major') {
            gradient = this.ctx.createLinearGradient(
                bubble.x - radius, bubble.y - radius,
                bubble.x + radius, bubble.y + radius
            );
            gradient.addColorStop(0, 'hsl(220, 100%, 60%)');
            gradient.addColorStop(1, 'hsl(240, 100%, 70%)');
        } else if (bubble.type === 'career') {
            gradient = this.ctx.createLinearGradient(
                bubble.x - radius, bubble.y - radius,
                bubble.x + radius, bubble.y + radius
            );
            gradient.addColorStop(0, 'hsl(140, 80%, 50%)');
            gradient.addColorStop(1, 'hsl(160, 90%, 60%)');
        } else {
            gradient = this.ctx.createLinearGradient(
                bubble.x - radius, bubble.y - radius,
                bubble.x + radius, bubble.y + radius
            );
            gradient.addColorStop(0, 'hsl(280, 90%, 60%)');
            gradient.addColorStop(1, 'hsl(300, 100%, 70%)');
        }

        // Draw bubble circle
        this.ctx.beginPath();
        this.ctx.arc(bubble.x, bubble.y, radius, 0, Math.PI * 2);
        this.ctx.fillStyle = gradient;
        this.ctx.fill();

        // Add shadow
        if (isHovered) {
            this.ctx.shadowBlur = 30;
            this.ctx.shadowColor = gradient;
            this.ctx.fill();
            this.ctx.shadowBlur = 0;
        }

        // Add highlight
        const highlightGradient = this.ctx.createRadialGradient(
            bubble.x - radius * 0.3,
            bubble.y - radius * 0.3,
            0,
            bubble.x,
            bubble.y,
            radius
        );
        highlightGradient.addColorStop(0, 'rgba(255, 255, 255, 0.3)');
        highlightGradient.addColorStop(0.5, 'rgba(255, 255, 255, 0.1)');
        highlightGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');

        this.ctx.beginPath();
        this.ctx.arc(bubble.x, bubble.y, radius, 0, Math.PI * 2);
        this.ctx.fillStyle = highlightGradient;
        this.ctx.fill();

        // Draw text
        this.ctx.fillStyle = 'white';
        this.ctx.font = 'bold 14px Inter, sans-serif';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
        this.ctx.shadowBlur = 4;

        // Wrap text if too long
        const maxWidth = radius * 1.6;
        const words = bubble.name.split(' ');
        let line = '';
        const lines = [];

        for (let word of words) {
            const testLine = line + word + ' ';
            const metrics = this.ctx.measureText(testLine);
            if (metrics.width > maxWidth && line !== '') {
                lines.push(line);
                line = word + ' ';
            } else {
                line = testLine;
            }
        }
        lines.push(line);

        // Draw lines
        const lineHeight = 18;
        const startY = bubble.y - (lines.length - 1) * lineHeight / 2;
        lines.forEach((line, i) => {
            this.ctx.fillText(line.trim(), bubble.x, startY + i * lineHeight);
        });

        this.ctx.shadowBlur = 0;
    }

    /**
     * Handle click events
     */
    handleClick(event) {
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // Check if any bubble was clicked
        for (let bubble of this.bubbles) {
            const dx = bubble.x - x;
            const dy = bubble.y - y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance <= bubble.radius) {
                this.onBubbleClick(bubble);
                break;
            }
        }
    }

    /**
     * Handle mouse move events (for hover effects)
     */
    handleMouseMove(event) {
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        let found = false;

        // Check if hovering over any bubble
        for (let bubble of this.bubbles) {
            const dx = bubble.x - x;
            const dy = bubble.y - y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance <= bubble.radius) {
                this.hoveredBubble = bubble;
                this.canvas.style.cursor = 'pointer';
                found = true;
                break;
            }
        }

        if (!found) {
            this.hoveredBubble = null;
            this.canvas.style.cursor = 'default';
        }
    }

    /**
     * Callback when a bubble is clicked (to be set externally)
     */
    onBubbleClick(bubble) {
        // This will be overridden by main.js
        console.log('Bubble clicked:', bubble);
    }
}

// Export for use in other scripts
window.BubbleEngine = BubbleEngine;

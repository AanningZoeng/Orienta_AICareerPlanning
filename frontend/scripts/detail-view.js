/**
 * Detail View - Manages detail modal content
 * Renders different content based on bubble type (major/career/future)
 */

class DetailView {
    constructor(modalId) {
        this.modal = document.getElementById(modalId);
        this.overlay = document.getElementById('modalOverlay');
        this.closeBtn = document.getElementById('modalClose');
        this.modalBody = document.getElementById('modalBody');

        // Bind events
        this.closeBtn.addEventListener('click', () => this.hide());
        this.overlay.addEventListener('click', () => this.hide());

        // Close on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.classList.contains('show')) {
                this.hide();
            }
        });
    }

    /**
     * Show the modal with specific content
     */
    show(bubble) {
        if (bubble.type === 'major') {
            this.renderMajorDetail(bubble.data);
        } else if (bubble.type === 'career') {
            this.renderCareerDetail(bubble.data);
        } else if (bubble.type === 'future') {
            this.renderFutureDetail(bubble.data);
        }

        this.modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    /**
     * Hide the modal
     */
    hide() {
        this.modal.classList.remove('show');
        document.body.style.overflow = '';
    }

    /**
     * Render major detail page
     */
    renderMajorDetail(major) {
        const universities = major.universities || [];
        const requirements = major.requirements || [];

        const html = `
            <div class="detail-major">
                <h2>${major.name}</h2>
                
                <div class="detail-section">
                    <h3>Overview</h3>
                    <p>${major.description}</p>
                </div>
                
                ${requirements.length > 0 ? `
                    <div class="detail-section">
                        <h3>Core Requirements</h3>
                        <ul class="requirements-list">
                            ${requirements.map(req => `<li>${req}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                
                <div class="detail-section">
                    <h3>Program Duration</h3>
                    <p>${major.duration || '4 years'}</p>
                </div>
                
                ${universities.length > 0 ? `
                    <div class="detail-section">
                        <h3>Top Universities</h3>
                        <ul class="universities-list">
                            ${universities.map(uni => `
                                <li>
                                    <a href="${uni.url}" target="_blank" rel="noopener">
                                        ${uni.name} →
                                    </a>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                ` : ''}
                
                ${major.video_url ? `
                    <div class="detail-section">
                        <h3>Learn More</h3>
                        <div class="video-embed">
                            <p style="color: var(--text-muted); margin-bottom: 1rem;">
                                Educational video about this major
                            </p>
                            <a href="${major.video_url}" target="_blank" style="color: hsl(220, 100%, 70%);">
                                Watch Video →
                            </a>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;

        this.modalBody.innerHTML = html;
    }

    /**
     * Render career detail page
     */
    renderCareerDetail(career) {
        const benefits = career.benefits || [];
        const resources = career.professional_resources || {};

        const html = `
            <div class="detail-career">
                <h2>${career.title}</h2>
                
                <div class="career-grid">
                    <div class="career-card">
                        <h4>Salary Range</h4>
                        <div class="value">${career.salary_range || 'N/A'}</div>
                    </div>
                    <div class="career-card">
                        <h4>Work Intensity</h4>
                        <div class="value">${career.work_intensity || 'N/A'}</div>
                    </div>
                    <div class="career-card">
                        <h4>Work-Life Balance</h4>
                        <div class="value">${career.work_life_balance || 'N/A'}</div>
                    </div>
                    <div class="career-card">
                        <h4>Growth Potential</h4>
                        <div class="value">${career.growth_potential || 'N/A'}</div>
                    </div>
                </div>
                
                ${benefits.length > 0 ? `
                    <div class="detail-section">
                        <h3>Common Benefits</h3>
                        <ul class="benefits-list">
                            ${benefits.map(benefit => `<li>${benefit}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                
                <div class="detail-section">
                    <h3>Job Outlook</h3>
                    <p>${career.job_outlook || 'N/A'}</p>
                </div>
                
                ${this.renderProfessionalResources(resources)}
            </div>
        `;

        this.modalBody.innerHTML = html;
    }

    /**
     * Render professional resources section
     */
    renderProfessionalResources(resources) {
        if (!resources || Object.keys(resources).length === 0) {
            return '';
        }

        let html = '<div class="detail-section"><h3>Professional Resources</h3><div class="resources-section">';

        // Videos
        if (resources.videos && resources.videos.length > 0) {
            html += `
                <div class="resource-category">
                    <h4>📺 YouTube Channels & Videos</h4>
                    ${resources.videos.map(video => `
                        <div class="resource-item">
                            <a href="${video.url}" target="_blank">${video.title}</a>
                            <small>${video.channel} • ${video.views} views</small>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        // Blogs
        if (resources.blogs && resources.blogs.length > 0) {
            html += `
                <div class="resource-category">
                    <h4>📝 Blogs & Articles</h4>
                    ${resources.blogs.map(blog => `
                        <div class="resource-item">
                            <a href="${blog.url}" target="_blank">${blog.title}</a>
                            <small>${blog.author} • ${blog.platform}</small>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        // Interviews
        if (resources.interviews && resources.interviews.length > 0) {
            html += `
                <div class="resource-category">
                    <h4>🎤 Interviews & Podcasts</h4>
                    ${resources.interviews.map(interview => `
                        <div class="resource-item">
                            <a href="${interview.url}" target="_blank">${interview.title}</a>
                            <small>${interview.source} • ${interview.duration}</small>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        html += '</div></div>';
        return html;
    }

    /**
     * Render future path detail page
     */
    renderFutureDetail(future) {
        const stats = future.statistics || {};
        const progressions = future.common_progressions || [];
        const insights = future.insights || [];

        const html = `
            <div class="detail-future">
                <h2>Future Path for ${future.career}</h2>
                
                <div class="detail-section">
                    <p style="color: var(--text-secondary); margin-bottom: 2rem;">
                        Career progression analysis over ${future.timeframe || '5 years'} based on ${future.sample_size || '10,000+'} professionals
                    </p>
                </div>
                
                <div class="stats-grid">
                    ${stats.promoted ? `
                        <div class="stat-card">
                            <div class="stat-percentage">${stats.promoted.percentage}%</div>
                            <div class="stat-label">Promoted</div>
                            <div class="stat-description">${stats.promoted.description || ''}</div>
                        </div>
                    ` : ''}
                    
                    ${stats.same_role ? `
                        <div class="stat-card">
                            <div class="stat-percentage">${stats.same_role.percentage}%</div>
                            <div class="stat-label">Same Role</div>
                            <div class="stat-description">${stats.same_role.description || ''}</div>
                        </div>
                    ` : ''}
                    
                    ${stats.changed_company ? `
                        <div class="stat-card">
                            <div class="stat-percentage">${stats.changed_company.percentage}%</div>
                            <div class="stat-label">Changed Company</div>
                            <div class="stat-description">${stats.changed_company.description || ''}</div>
                        </div>
                    ` : ''}
                    
                    ${stats.changed_career ? `
                        <div class="stat-card">
                            <div class="stat-percentage">${stats.changed_career.percentage}%</div>
                            <div class="stat-label">Changed Career</div>
                            <div class="stat-description">${stats.changed_career.description || ''}</div>
                        </div>
                    ` : ''}
                    
                    ${stats.laid_off ? `
                        <div class="stat-card">
                            <div class="stat-percentage">${stats.laid_off.percentage}%</div>
                            <div class="stat-label">Laid Off</div>
                            <div class="stat-description">${stats.laid_off.description || ''}</div>
                        </div>
                    ` : ''}
                </div>
                
                ${progressions.length > 0 ? `
                    <div class="detail-section">
                        <h3>Common Career Progressions</h3>
                        <ul class="progressions-list">
                            ${progressions.map(prog => `<li>${prog}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                
                ${future.salary_growth ? `
                    <div class="detail-section">
                        <h3>Average Salary Growth</h3>
                        <p style="font-size: 1.2rem; color: hsl(140, 80%, 60%);">
                            ${future.salary_growth}
                        </p>
                    </div>
                ` : ''}
                
                ${insights.length > 0 ? `
                    <div class="detail-section">
                        <h3>Key Insights</h3>
                        <ul class="insights-list">
                            ${insights.map(insight => `<li>${insight}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;

        this.modalBody.innerHTML = html;
    }
}

// Export for use in other scripts
window.DetailView = DetailView;

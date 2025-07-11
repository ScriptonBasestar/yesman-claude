/**
 * HealthWidget Component
 * Web component for displaying project health metrics and scores
 */
class HealthWidget extends HTMLElement {
    constructor() {
        super();
        this.health = null;
        this.refreshInterval = null;
    }

    connectedCallback() {
        this.render();
        this.loadHealth();
        this.setupRealtimeUpdates();
        
        // Auto-refresh every 60 seconds as fallback
        this.refreshInterval = setInterval(() => {
            if (!window.dashboard?.state?.wsConnected) {
                this.loadHealth();
            }
        }, 60000);
    }

    disconnectedCallback() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        this.cleanup();
    }
    
    setupRealtimeUpdates() {
        // Listen for WebSocket updates
        this.healthUpdateHandler = (event) => {
            const data = event.detail?.data || {};
            this.updateHealth(data);
        };
        
        window.addEventListener('health-updated', this.healthUpdateHandler);
    }
    
    cleanup() {
        if (this.healthUpdateHandler) {
            window.removeEventListener('health-updated', this.healthUpdateHandler);
        }
    }

    async loadHealth() {
        try {
            const response = await axios.get('/api/dashboard/health');
            this.health = response.data;
            this.renderHealth();
        } catch (error) {
            console.error('Failed to load health data:', error);
            this.renderError('Failed to load health data');
        }
    }

    updateHealth(healthData) {
        if (!healthData || JSON.stringify(this.health) === JSON.stringify(healthData)) {
            return; // No change needed
        }
        
        const oldHealth = this.health;
        this.health = healthData;
        
        // Apply incremental updates with animation
        this.applyHealthUpdatesWithAnimation(oldHealth, healthData);
    }
    
    applyHealthUpdatesWithAnimation(oldHealth, newHealth) {
        // Update overall score with animation
        const scoreElement = this.querySelector('.score-number');
        if (scoreElement && oldHealth?.overall_score !== newHealth?.overall_score) {
            scoreElement.style.animation = 'pulse 0.5s ease-out';
            setTimeout(() => {
                scoreElement.dataset.score = newHealth.overall_score || 0;
                this.animateScoreNumber();
            }, 100);
        }
        
        // Update category progress bars
        const oldCategories = oldHealth?.categories || {};
        const newCategories = newHealth?.categories || {};
        
        Object.keys(newCategories).forEach(category => {
            if (oldCategories[category] !== newCategories[category]) {
                const categoryElement = this.querySelector(`[data-category="${category}"]`);
                if (categoryElement) {
                    const progressBar = categoryElement.querySelector('.progress-bar');
                    if (progressBar) {
                        progressBar.style.animation = 'pulse 0.3s ease-out';
                        setTimeout(() => {
                            progressBar.dataset.width = newCategories[category];
                            progressBar.style.width = `${newCategories[category]}%`;
                        }, 150);
                    }
                }
            }
        });
        
        // If significant changes, do a full re-render
        if (!oldHealth || 
            Math.abs((oldHealth.overall_score || 0) - (newHealth.overall_score || 0)) > 10) {
            setTimeout(() => this.renderHealth(), 500);
        }
    }

    getScoreColor(score) {
        if (score >= 80) return 'text-green-600';
        if (score >= 60) return 'text-yellow-600';
        return 'text-red-600';
    }

    getProgressColor(score) {
        if (score >= 80) return 'bg-green-500';
        if (score >= 60) return 'bg-yellow-500';
        return 'bg-red-500';
    }

    getOverallScoreBackground(score) {
        if (score >= 80) return 'bg-green-100 dark:bg-green-900/20';
        if (score >= 60) return 'bg-yellow-100 dark:bg-yellow-900/20';
        return 'bg-red-100 dark:bg-red-900/20';
    }

    render() {
        this.innerHTML = `
            <div class="health-widget">
                <!-- Loading state -->
                <div class="loading text-center py-8">
                    <svg class="animate-spin h-8 w-8 mx-auto mb-2 text-gray-400" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <div class="text-gray-500 dark:text-gray-400">Loading health data...</div>
                </div>
            </div>
        `;
    }

    renderHealth() {
        if (!this.health) {
            this.renderError('No health data available');
            return;
        }

        const overallScore = this.health.overall_score || 0;
        const categories = this.health.categories || {};
        const suggestions = this.health.suggestions || [];

        this.innerHTML = `
            <div class="health-widget space-y-6">
                <!-- Overall Score -->
                <div class="overall-score text-center p-6 rounded-lg ${this.getOverallScoreBackground(overallScore)}">
                    <div class="mb-2">
                        <div class="text-sm font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">
                            Project Health
                        </div>
                    </div>
                    <div class="score-display flex items-center justify-center space-x-4">
                        <div class="score-number ${this.getScoreColor(overallScore)} text-4xl font-bold" 
                             data-score="${overallScore}" 
                             role="progressbar" 
                             aria-valuenow="${overallScore}" 
                             aria-valuemin="0" 
                             aria-valuemax="100"
                             aria-label="Overall health score">
                            ${Math.round(overallScore)}
                        </div>
                        <div class="score-indicator">
                            <svg class="w-12 h-12 ${this.getScoreColor(overallScore)}" fill="currentColor" viewBox="0 0 24 24">
                                ${this.getScoreIcon(overallScore)}
                            </svg>
                        </div>
                    </div>
                    <div class="mt-2 text-sm text-gray-600 dark:text-gray-400">
                        ${this.getScoreDescription(overallScore)}
                    </div>
                </div>

                <!-- Category Scores -->
                <div class="categories space-y-3">
                    <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
                        Category Breakdown
                    </h4>
                    <div class="category-list space-y-3">
                        ${this.renderCategories(categories)}
                    </div>
                </div>

                <!-- Suggestions -->
                ${suggestions.length > 0 ? `
                    <div class="suggestions">
                        <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide mb-3">
                            Improvement Suggestions
                        </h4>
                        <div class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                            <ul class="space-y-2">
                                ${suggestions.slice(0, 3).map(suggestion => `
                                    <li class="flex items-start space-x-2">
                                        <svg class="w-4 h-4 text-yellow-600 dark:text-yellow-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                                        </svg>
                                        <span class="text-sm text-yellow-800 dark:text-yellow-200">${suggestion}</span>
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    </div>
                ` : ''}

                <!-- Last Updated -->
                <div class="last-updated text-center">
                    <div class="text-xs text-gray-500 dark:text-gray-400">
                        Last updated: ${new Date().toLocaleTimeString()}
                    </div>
                </div>
            </div>
        `;

        // Trigger progress bar animations
        this.animateProgressBars();
    }

    renderCategories(categories) {
        const categoryNames = {
            build: 'Build System',
            tests: 'Test Coverage',
            dependencies: 'Dependencies',
            security: 'Security',
            performance: 'Performance',
            code_quality: 'Code Quality',
            git: 'Git Health',
            documentation: 'Documentation'
        };

        return Object.entries(categories).map(([key, score]) => {
            const name = categoryNames[key] || key.replace('_', ' ');
            const normalizedScore = Math.max(0, Math.min(100, score || 0));
            
            return `
                <div class="category-item" data-category="${key}">
                    <div class="flex items-center justify-between mb-1">
                        <span class="text-sm font-medium text-gray-700 dark:text-gray-300">${name}</span>
                        <span class="text-sm font-semibold ${this.getScoreColor(normalizedScore)}">${Math.round(normalizedScore)}</span>
                    </div>
                    <div class="progress-container">
                        <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div class="progress-bar h-2 rounded-full transition-all duration-1000 ease-out ${this.getProgressColor(normalizedScore)}" 
                                 data-width="${normalizedScore}" 
                                 style="width: 0%"
                                 role="progressbar" 
                                 aria-valuenow="${normalizedScore}" 
                                 aria-valuemin="0" 
                                 aria-valuemax="100"
                                 aria-label="${name} score: ${normalizedScore}%">
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    getScoreIcon(score) {
        if (score >= 80) {
            return '<path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>';
        } else if (score >= 60) {
            return '<path d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>';
        } else {
            return '<path d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/>';
        }
    }

    getScoreDescription(score) {
        if (score >= 80) return 'Excellent project health';
        if (score >= 60) return 'Good project health';
        if (score >= 40) return 'Fair project health';
        return 'Needs attention';
    }

    animateProgressBars() {
        // Animate progress bars with a slight delay
        setTimeout(() => {
            const progressBars = this.querySelectorAll('.progress-bar');
            progressBars.forEach((bar, index) => {
                setTimeout(() => {
                    const targetWidth = bar.dataset.width;
                    bar.style.width = `${targetWidth}%`;
                }, index * 100);
            });
        }, 100);

        // Animate score number count-up (optional)
        this.animateScoreNumber();
    }

    animateScoreNumber() {
        const scoreElement = this.querySelector('.score-number');
        if (!scoreElement) return;

        const targetScore = parseInt(scoreElement.dataset.score) || 0;
        const duration = 1000; // 1 second
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function for smooth animation
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const currentScore = Math.round(targetScore * easeOut);
            
            scoreElement.textContent = currentScore;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    renderError(message) {
        this.innerHTML = `
            <div class="health-widget-error text-center py-8">
                <svg class="w-12 h-12 mx-auto mb-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">Unable to Load Health Data</h3>
                <p class="text-gray-500 dark:text-gray-400">${message}</p>
                <button 
                    onclick="this.closest('health-widget').loadHealth()"
                    class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                    Retry
                </button>
            </div>
        `;
    }
}

// Register the custom element
customElements.define('health-widget', HealthWidget);
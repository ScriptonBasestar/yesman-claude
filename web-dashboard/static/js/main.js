/**
 * Yesman Claude Web Dashboard - Main JavaScript Module
 * 
 * This module provides the core JavaScript functionality for the web dashboard,
 * including global state management, API communication, and utility functions.
 */

// Global dashboard object
window.dashboard = {
    // Application state
    state: {
        sessions: [],
        health: {},
        activity: {},
        stats: {},
        theme: localStorage.getItem('theme') || 'light',
        loading: false,
        error: null,
        initialized: false
    },

    // API client methods
    api: {
        baseURL: '/web/api',
        
        /**
         * Generic API request handler with error handling and retry logic
         */
        async request(endpoint, options = {}) {
            const defaultOptions = {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                retries: 3,
                retryDelay: 1000,
                timeout: 10000
            };

            const config = { ...defaultOptions, ...options };
            let lastError;

            for (let attempt = 0; attempt <= config.retries; attempt++) {
                try {
                    // Create AbortController for timeout
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), config.timeout);

                    const response = await fetch(`${this.baseURL}${endpoint}`, {
                        method: config.method,
                        headers: config.headers,
                        body: config.body ? JSON.stringify(config.body) : undefined,
                        signal: controller.signal
                    });

                    clearTimeout(timeoutId);

                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }

                    const data = await response.json();
                    return data;

                } catch (error) {
                    lastError = error;
                    
                    // Handle different error types
                    if (error.name === 'AbortError') {
                        lastError = new Error('Request timeout');
                    }
                    
                    // Don't retry on client errors (4xx)
                    if (error.message.includes('HTTP 4')) {
                        break;
                    }

                    // Log retry attempts
                    if (attempt < config.retries) {
                        console.warn(`Retrying ${endpoint} (attempt ${attempt + 1}/${config.retries})...`);
                        await new Promise(resolve => setTimeout(resolve, config.retryDelay * (attempt + 1)));
                    }
                }
            }

            // Add endpoint to error for better debugging
            lastError.endpoint = endpoint;
            throw lastError;
        },

        /**
         * Get sessions list
         */
        async getSessions() {
            try {
                const data = await this.request('/sessions');
                window.dashboard.state.sessions = data.sessions || [];
                return data;
            } catch (error) {
                console.error('Failed to fetch sessions:', error);
                window.dashboard.state.error = error.message;
                throw error;
            }
        },

        /**
         * Get project health metrics
         */
        async getHealth() {
            try {
                const data = await this.request('/health');
                window.dashboard.state.health = data;
                return data;
            } catch (error) {
                console.error('Failed to fetch health data:', error);
                window.dashboard.state.error = error.message;
                throw error;
            }
        },

        /**
         * Get activity data
         */
        async getActivity() {
            try {
                const data = await this.request('/activity');
                window.dashboard.state.activity = data;
                return data;
            } catch (error) {
                console.error('Failed to fetch activity data:', error);
                window.dashboard.state.error = error.message;
                throw error;
            }
        },

        /**
         * Get dashboard statistics
         */
        async getStats() {
            try {
                const data = await this.request('/stats');
                window.dashboard.state.stats = data;
                return data;
            } catch (error) {
                console.error('Failed to fetch stats:', error);
                window.dashboard.state.error = error.message;
                throw error;
            }
        },

        /**
         * Load all dashboard data
         */
        async loadAll() {
            window.dashboard.state.loading = true;
            window.dashboard.state.error = null;

            try {
                const [sessions, health, activity, stats] = await Promise.allSettled([
                    this.getSessions(),
                    this.getHealth(),
                    this.getActivity(),
                    this.getStats()
                ]);

                // Log any failed requests
                [sessions, health, activity, stats].forEach((result, index) => {
                    if (result.status === 'rejected') {
                        const endpoints = ['sessions', 'health', 'activity', 'stats'];
                        console.warn(`Failed to load ${endpoints[index]}:`, result.reason);
                    }
                });

                return true;
            } catch (error) {
                console.error('Failed to load dashboard data:', error);
                window.dashboard.state.error = error.message;
                return false;
            } finally {
                window.dashboard.state.loading = false;
            }
        }
    },

    // Utility functions
    utils: {
        /**
         * Format date string to readable format
         */
        formatDate(dateString, options = {}) {
            if (!dateString) return 'N/A';

            try {
                const date = new Date(dateString);
                const defaultOptions = {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                };

                return date.toLocaleDateString('en-US', { ...defaultOptions, ...options });
            } catch (error) {
                console.error('Invalid date format:', dateString);
                return 'Invalid Date';
            }
        },

        /**
         * Format relative time (e.g., "2 hours ago")
         */
        formatRelativeTime(dateString) {
            if (!dateString) return 'Unknown';

            try {
                const date = new Date(dateString);
                const now = new Date();
                const diff = now - date;

                const seconds = Math.floor(diff / 1000);
                const minutes = Math.floor(seconds / 60);
                const hours = Math.floor(minutes / 60);
                const days = Math.floor(hours / 24);

                if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
                if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
                if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
                return 'Just now';
            } catch (error) {
                console.error('Invalid date format:', dateString);
                return 'Unknown';
            }
        },

        /**
         * Toggle theme between light and dark
         */
        toggleTheme() {
            const currentTheme = window.dashboard.state.theme;
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            window.dashboard.state.theme = newTheme;
            localStorage.setItem('theme', newTheme);
            
            // Update DOM
            document.documentElement.classList.toggle('dark', newTheme === 'dark');
            
            // Dispatch custom event
            window.dispatchEvent(new CustomEvent('theme-changed', { 
                detail: { theme: newTheme } 
            }));
            
            return newTheme;
        },

        /**
         * Initialize theme based on localStorage or system preference
         */
        initializeTheme() {
            const savedTheme = localStorage.getItem('theme');
            const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            
            let theme = savedTheme;
            if (!theme) {
                theme = systemPrefersDark ? 'dark' : 'light';
            }
            
            window.dashboard.state.theme = theme;
            document.documentElement.classList.toggle('dark', theme === 'dark');
            
            // Listen for system theme changes
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (!localStorage.getItem('theme')) {
                    const newTheme = e.matches ? 'dark' : 'light';
                    window.dashboard.state.theme = newTheme;
                    document.documentElement.classList.toggle('dark', newTheme === 'dark');
                }
            });
        },

        /**
         * Debounce function execution
         */
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        /**
         * Throttle function execution
         */
        throttle(func, limit) {
            let inThrottle;
            return function(...args) {
                if (!inThrottle) {
                    func.apply(this, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        },

        /**
         * Format bytes to human readable string
         */
        formatBytes(bytes, decimals = 2) {
            if (bytes === 0) return '0 Bytes';

            const k = 1024;
            const dm = decimals < 0 ? 0 : decimals;
            const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];

            const i = Math.floor(Math.log(bytes) / Math.log(k));

            return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
        },

        /**
         * Generate unique ID
         */
        generateId() {
            return Date.now().toString(36) + Math.random().toString(36).substr(2);
        },

        /**
         * Show toast notification
         */
        showToast(message, type = 'info', duration = 3000) {
            const toast = document.createElement('div');
            toast.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300 ${
                type === 'error' ? 'bg-red-500 text-white' :
                type === 'success' ? 'bg-green-500 text-white' :
                type === 'warning' ? 'bg-yellow-500 text-black' :
                'bg-blue-500 text-white'
            }`;
            toast.textContent = message;
            
            document.body.appendChild(toast);
            
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    document.body.removeChild(toast);
                }, 300);
            }, duration);
        }
    },

    // Alpine.js component factory
    components: {
        /**
         * Main dashboard component
         */
        dashboard() {
            return {
                loading: false,
                error: null,
                stats: {
                    active_sessions: 0,
                    health_score: 0,
                    total_projects: 0,
                    activity_streak: 0
                },

                async init() {
                    this.loading = true;
                    try {
                        await window.dashboard.api.loadAll();
                        this.stats = window.dashboard.state.stats;
                    } catch (error) {
                        this.error = error.message;
                        window.dashboard.utils.showToast('Failed to load dashboard data', 'error');
                    } finally {
                        this.loading = false;
                    }
                },

                async refresh() {
                    await this.init();
                },

                toggleTheme() {
                    window.dashboard.utils.toggleTheme();
                }
            };
        },

        /**
         * Session browser component
         */
        sessionBrowser() {
            return {
                sessions: [],
                loading: false,
                error: null,
                selectedSession: null,

                async init() {
                    await this.loadSessions();
                },

                async loadSessions() {
                    this.loading = true;
                    try {
                        const data = await window.dashboard.api.getSessions();
                        this.sessions = data.sessions || [];
                    } catch (error) {
                        this.error = error.message;
                    } finally {
                        this.loading = false;
                    }
                },

                selectSession(session) {
                    this.selectedSession = session;
                },

                getSessionStatus(session) {
                    return session.claude_active ? 'active' : 'inactive';
                }
            };
        },

        /**
         * Health widget component
         */
        healthWidget() {
            return {
                health: {},
                loading: false,
                error: null,

                async init() {
                    await this.loadHealth();
                },

                async loadHealth() {
                    this.loading = true;
                    try {
                        this.health = await window.dashboard.api.getHealth();
                    } catch (error) {
                        this.error = error.message;
                    } finally {
                        this.loading = false;
                    }
                },

                getHealthColor(score) {
                    if (score >= 80) return 'text-green-600';
                    if (score >= 60) return 'text-yellow-600';
                    return 'text-red-600';
                }
            };
        },

        /**
         * Activity heatmap component
         */
        activityHeatmap() {
            return {
                activity: {},
                loading: false,
                error: null,

                async init() {
                    await this.loadActivity();
                },

                async loadActivity() {
                    this.loading = true;
                    try {
                        this.activity = await window.dashboard.api.getActivity();
                    } catch (error) {
                        this.error = error.message;
                    } finally {
                        this.loading = false;
                    }
                },

                getActivityLevel(count) {
                    if (count === 0) return 'bg-gray-100 dark:bg-gray-800';
                    if (count <= 3) return 'bg-green-200 dark:bg-green-900';
                    if (count <= 7) return 'bg-green-400 dark:bg-green-700';
                    if (count <= 12) return 'bg-green-600 dark:bg-green-500';
                    return 'bg-green-800 dark:bg-green-400';
                }
            };
        }
    },

    // Initialize dashboard
    async init() {
        if (window.dashboard.state.initialized) {
            return;
        }

        try {
            // Initialize theme
            window.dashboard.utils.initializeTheme();

            // Load initial data
            await window.dashboard.api.loadAll();

            // Set up periodic refresh
            setInterval(async () => {
                try {
                    await window.dashboard.api.loadAll();
                } catch (error) {
                    console.error('Failed to refresh dashboard data:', error);
                }
            }, 30000); // Refresh every 30 seconds

            window.dashboard.state.initialized = true;
            console.log('Dashboard initialized successfully');

        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
            window.dashboard.state.error = error.message;
        }
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard.init();
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.dashboard;
}
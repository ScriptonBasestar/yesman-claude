/**
 * Yesman Claude Web Dashboard - Main JavaScript Module
 * 
 * This module provides the core JavaScript functionality for the web dashboard,
 * including global state management, API communication, and utility functions.
 */

// Import WebSocket manager
const wsManager = window.wsManager || new WebSocketManager();

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
        initialized: false,
        wsConnected: false
    },
    
    // WebSocket manager reference
    ws: wsManager,

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
            const container = document.getElementById('toast-container') || this.createToastContainer();
            const toastId = this.generateId();
            
            const toast = document.createElement('div');
            toast.id = toastId;
            toast.className = `toast toast-${type} opacity-0 translate-x-full`;
            
            // Icon
            const iconSvg = {
                success: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>',
                error: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>',
                warning: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>',
                info: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>'
            };
            
            toast.innerHTML = `
                <svg class="toast-icon ${
                    type === 'success' ? 'text-green-500' :
                    type === 'error' ? 'text-red-500' :
                    type === 'warning' ? 'text-yellow-500' :
                    'text-blue-500'
                }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    ${iconSvg[type] || iconSvg.info}
                </svg>
                <div class="toast-message">${message}</div>
                <button class="toast-close" onclick="window.dashboard.utils.removeToast('${toastId}')">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            `;
            
            container.appendChild(toast);
            
            // Trigger animation
            requestAnimationFrame(() => {
                toast.classList.remove('opacity-0', 'translate-x-full');
                toast.classList.add('opacity-100', 'translate-x-0');
            });
            
            // Auto remove
            if (duration > 0) {
                setTimeout(() => {
                    this.removeToast(toastId);
                }, duration);
            }
            
            return toastId;
        },
        
        /**
         * Remove toast notification
         */
        removeToast(toastId) {
            const toast = document.getElementById(toastId);
            if (toast) {
                toast.classList.add('opacity-0', 'translate-x-full');
                setTimeout(() => {
                    toast.remove();
                }, 300);
            }
        },
        
        /**
         * Create toast container if it doesn't exist
         */
        createToastContainer() {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
            return container;
        },
        
        /**
         * Update connection status indicator
         */
        updateConnectionStatus(status) {
            const statusElement = document.getElementById('connection-status');
            const dotElement = statusElement?.querySelector('.connection-dot');
            const textElement = statusElement?.querySelector('.connection-text');
            
            if (!statusElement) return;
            
            // Remove all status classes
            statusElement.classList.remove('connected', 'disconnected', 'reconnecting');
            dotElement?.classList.remove('connected', 'disconnected', 'reconnecting');
            
            // Add new status
            statusElement.classList.add(status);
            dotElement?.classList.add(status);
            
            // Update text
            if (textElement) {
                switch (status) {
                    case 'connected':
                        textElement.textContent = 'Connected';
                        break;
                    case 'reconnecting':
                        textElement.textContent = 'Reconnecting...';
                        break;
                    case 'disconnected':
                        textElement.textContent = 'Disconnected';
                        break;
                }
            }
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
            
            // Initialize WebSocket connection
            window.dashboard.initWebSocket();

            // Load initial data
            await window.dashboard.api.loadAll();

            // Set up periodic refresh (reduced frequency due to WebSocket)
            setInterval(async () => {
                try {
                    // Only refresh if WebSocket is not connected
                    if (!window.dashboard.state.wsConnected) {
                        await window.dashboard.api.loadAll();
                    }
                } catch (error) {
                    console.error('Failed to refresh dashboard data:', error);
                }
            }, 60000); // Refresh every 60 seconds as fallback

            window.dashboard.state.initialized = true;
            console.log('Dashboard initialized successfully');

        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
            window.dashboard.state.error = error.message;
        }
    },
    
    // Initialize WebSocket connections
    initWebSocket() {
        // Enable debug mode in development
        if (window.location.hostname === 'localhost') {
            wsManager.setDebug(true);
        }
        
        // Connect to dashboard channel
        wsManager.connect('dashboard');
        
        // Set up event handlers
        wsManager.on('connected', (data) => {
            console.log('WebSocket connected:', data);
            window.dashboard.state.wsConnected = true;
            window.dashboard.utils.updateConnectionStatus('connected');
            window.dashboard.utils.showToast('Real-time updates connected', 'success', 2000);
        });
        
        wsManager.on('disconnected', (data) => {
            console.log('WebSocket disconnected:', data);
            window.dashboard.state.wsConnected = false;
            window.dashboard.utils.updateConnectionStatus('disconnected');
            if (data.code !== 1000) { // Not a normal closure
                window.dashboard.utils.showToast('Real-time updates disconnected', 'warning');
            }
        });
        
        wsManager.on('reconnecting', (data) => {
            console.log('WebSocket reconnecting:', data);
            window.dashboard.utils.updateConnectionStatus('reconnecting');
            if (data.attempt === 1) {
                window.dashboard.utils.showToast('Reconnecting to server...', 'info', 2000);
            }
        });
        
        wsManager.on('session_update', (data) => {
            console.log('Session update received:', data);
            window.dashboard.state.sessions = data.data || [];
            // Dispatch custom event for components
            window.dispatchEvent(new CustomEvent('sessions-updated', { detail: data }));
        });
        
        wsManager.on('health_update', (data) => {
            console.log('Health update received:', data);
            window.dashboard.state.health = data.data || {};
            // Dispatch custom event for components
            window.dispatchEvent(new CustomEvent('health-updated', { detail: data }));
        });
        
        wsManager.on('activity_update', (data) => {
            console.log('Activity update received:', data);
            window.dashboard.state.activity = data.data || {};
            // Dispatch custom event for components
            window.dispatchEvent(new CustomEvent('activity-updated', { detail: data }));
        });
        
        wsManager.on('initial_data', (data) => {
            console.log('Initial data received:', data);
            const initialData = data.data || {};
            
            if (initialData.sessions) {
                window.dashboard.state.sessions = initialData.sessions;
            }
            if (initialData.health) {
                window.dashboard.state.health = initialData.health;
            }
            if (initialData.activity) {
                window.dashboard.state.activity = initialData.activity;
            }
            if (initialData.stats) {
                window.dashboard.state.stats = initialData.stats;
            }
        });
        
        wsManager.on('error', (data) => {
            console.error('WebSocket error:', data);
            window.dashboard.utils.showToast('Connection error', 'error');
        });
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
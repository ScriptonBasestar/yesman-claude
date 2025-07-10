/**
 * LogViewer Component
 * Real-time log streaming and display component with filtering and controls
 */
class LogViewer extends HTMLElement {
    constructor() {
        super();
        this.logs = [];
        this.filteredLogs = [];
        this.maxLogs = 1000;
        this.filters = {
            level: 'all',
            source: 'all',
            search: '',
            since: null
        };
        this.isPaused = false;
        this.autoScroll = true;
        this.refreshInterval = null;
        this.visibleRange = { start: 0, end: 50 }; // Virtual scrolling
    }

    connectedCallback() {
        this.render();
        this.bindEvents();
        this.setupRealtimeUpdates();
        this.startRefreshTimer();
        this.loadLogs();
    }

    disconnectedCallback() {
        this.cleanup();
    }

    setupRealtimeUpdates() {
        // Listen for WebSocket log updates
        this.logUpdateHandler = (event) => {
            if (!this.isPaused) {
                const logData = event.detail?.data;
                if (logData) {
                    this.addLog(logData);
                }
            }
        };
        
        window.addEventListener('log-updated', this.logUpdateHandler);
    }

    cleanup() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        if (this.logUpdateHandler) {
            window.removeEventListener('log-updated', this.logUpdateHandler);
        }
    }

    startRefreshTimer() {
        // Update relative timestamps every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.updateTimestamps();
        }, 30000);
    }

    addLog(logEntry) {
        // Ensure log entry has required fields
        const log = {
            id: Date.now() + Math.random(),
            level: logEntry.level || 'info',
            timestamp: logEntry.timestamp || new Date().toISOString(),
            source: logEntry.source || 'unknown',
            message: logEntry.message || '',
            raw: logEntry.raw || logEntry.message || ''
        };

        this.logs.push(log);

        // Enforce max logs limit
        if (this.logs.length > this.maxLogs) {
            this.logs.splice(0, this.logs.length - this.maxLogs);
        }

        // Apply filters and re-render if needed
        this.applyFilters();
        
        // Auto-scroll to bottom if enabled
        if (this.autoScroll && !this.isPaused) {
            setTimeout(() => this.scrollToBottom(), 50);
        }
    }

    addLogs(logEntries) {
        logEntries.forEach(log => this.addLog(log));
    }

    setFilter(filterType, value) {
        this.filters[filterType] = value;
        this.applyFilters();
        this.updateFilterUI();
    }

    applyFilters() {
        this.filteredLogs = this.logs.filter(log => {
            // Level filter
            if (this.filters.level !== 'all' && log.level !== this.filters.level) {
                return false;
            }

            // Source filter
            if (this.filters.source !== 'all' && log.source !== this.filters.source) {
                return false;
            }

            // Text search filter
            if (this.filters.search && !log.message.toLowerCase().includes(this.filters.search.toLowerCase())) {
                return false;
            }

            // Time filter
            if (this.filters.since) {
                const logTime = new Date(log.timestamp);
                if (logTime < this.filters.since) {
                    return false;
                }
            }

            return true;
        });

        this.renderLogs();
    }

    clearLogs() {
        this.logs = [];
        this.filteredLogs = [];
        this.renderLogs();
    }

    togglePause() {
        this.isPaused = !this.isPaused;
        this.updateControlsUI();
    }

    toggleAutoScroll() {
        this.autoScroll = !this.autoScroll;
        this.updateControlsUI();
        if (this.autoScroll) {
            this.scrollToBottom();
        }
    }

    scrollToBottom() {
        const container = this.querySelector('.log-container');
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    }

    getLevelColor(level) {
        const colors = {
            error: 'text-red-600 bg-red-50 dark:bg-red-900/20 dark:text-red-400',
            warning: 'text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20 dark:text-yellow-400',
            info: 'text-blue-600 bg-blue-50 dark:bg-blue-900/20 dark:text-blue-400',
            debug: 'text-gray-600 bg-gray-50 dark:bg-gray-900/20 dark:text-gray-400',
            success: 'text-green-600 bg-green-50 dark:bg-green-900/20 dark:text-green-400'
        };
        return colors[level] || colors.info;
    }

    getLevelIcon(level) {
        const icons = {
            error: '🔴',
            warning: '🟡',
            info: '🔵',
            debug: '⚪',
            success: '🟢'
        };
        return icons[level] || icons.info;
    }

    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;

        // Less than 1 minute ago
        if (diff < 60000) {
            return 'just now';
        }
        
        // Less than 1 hour ago
        if (diff < 3600000) {
            const minutes = Math.floor(diff / 60000);
            return `${minutes}m ago`;
        }
        
        // Less than 24 hours ago
        if (diff < 86400000) {
            const hours = Math.floor(diff / 3600000);
            return `${hours}h ago`;
        }
        
        // More than 24 hours ago - show full timestamp
        return date.toLocaleString();
    }

    highlightSearchTerm(text, searchTerm) {
        if (!searchTerm) return text;
        
        const regex = new RegExp(`(${searchTerm})`, 'gi');
        return text.replace(regex, '<mark class="bg-yellow-300 dark:bg-yellow-600">$1</mark>');
    }

    getUniqueSources() {
        const sources = new Set(this.logs.map(log => log.source));
        return Array.from(sources).sort();
    }

    bindEvents() {
        // Control buttons
        this.addEventListener('click', (e) => {
            if (e.target.matches('[data-action]')) {
                const action = e.target.dataset.action;
                this.handleAction(action);
            }
        });

        // Filter inputs
        this.addEventListener('change', (e) => {
            if (e.target.matches('[data-filter]')) {
                const filterType = e.target.dataset.filter;
                const value = e.target.value;
                this.setFilter(filterType, value);
            }
        });

        // Search input
        this.addEventListener('input', (e) => {
            if (e.target.matches('[data-filter="search"]')) {
                const value = e.target.value;
                this.setFilter('search', value);
            }
        });

        // Scroll handling for auto-scroll detection
        this.addEventListener('scroll', (e) => {
            if (e.target.matches('.log-container')) {
                const container = e.target;
                const isAtBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 50;
                
                if (!isAtBottom && this.autoScroll) {
                    this.autoScroll = false;
                    this.updateControlsUI();
                }
            }
        });
    }

    handleAction(action) {
        switch (action) {
            case 'pause':
                this.togglePause();
                break;
            case 'clear':
                this.clearLogs();
                break;
            case 'auto-scroll':
                this.toggleAutoScroll();
                break;
            case 'export':
                this.exportLogs();
                break;
            default:
                console.warn('Unknown action:', action);
        }
    }

    exportLogs() {
        const logText = this.filteredLogs.map(log => 
            `[${log.timestamp}] [${log.level.toUpperCase()}] [${log.source}] ${log.message}`
        ).join('\n');
        
        const blob = new Blob([logText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `logs-${new Date().toISOString().split('T')[0]}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }

    updateTimestamps() {
        const timestampElements = this.querySelectorAll('.log-timestamp');
        timestampElements.forEach((element, index) => {
            if (this.filteredLogs[index]) {
                element.textContent = this.formatTimestamp(this.filteredLogs[index].timestamp);
            }
        });
    }

    updateFilterUI() {
        // Update filter dropdowns and inputs
        const levelSelect = this.querySelector('[data-filter="level"]');
        if (levelSelect) {
            levelSelect.value = this.filters.level;
        }

        const sourceSelect = this.querySelector('[data-filter="source"]');
        if (sourceSelect) {
            sourceSelect.value = this.filters.source;
        }

        const searchInput = this.querySelector('[data-filter="search"]');
        if (searchInput) {
            searchInput.value = this.filters.search;
        }
    }

    updateControlsUI() {
        // Update pause button
        const pauseBtn = this.querySelector('[data-action="pause"]');
        if (pauseBtn) {
            pauseBtn.innerHTML = this.isPaused ? 
                '<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M8 5v10l7-5-7-5z"/></svg> Resume' :
                '<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M6 4h2v12H6V4zm6 0h2v12h-2V4z"/></svg> Pause';
            pauseBtn.className = `px-3 py-1 text-sm rounded-md flex items-center space-x-1 ${
                this.isPaused ? 'bg-green-600 text-white hover:bg-green-700' : 'bg-yellow-600 text-white hover:bg-yellow-700'
            }`;
        }

        // Update auto-scroll button
        const scrollBtn = this.querySelector('[data-action="auto-scroll"]');
        if (scrollBtn) {
            scrollBtn.className = `px-3 py-1 text-sm rounded-md flex items-center space-x-1 ${
                this.autoScroll ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-gray-600 text-white hover:bg-gray-700'
            }`;
        }
    }

    render() {
        this.innerHTML = `
            <div class="log-viewer">
                <!-- Header Controls -->
                <div class="log-controls flex flex-wrap items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                    <!-- Filter Controls -->
                    <div class="filters flex flex-wrap items-center space-x-4">
                        <!-- Level Filter -->
                        <div class="filter-group">
                            <label class="text-xs text-gray-600 dark:text-gray-400">Level</label>
                            <select data-filter="level" class="ml-1 text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-700">
                                <option value="all">All</option>
                                <option value="error">Error</option>
                                <option value="warning">Warning</option>
                                <option value="info">Info</option>
                                <option value="debug">Debug</option>
                            </select>
                        </div>
                        
                        <!-- Source Filter -->
                        <div class="filter-group">
                            <label class="text-xs text-gray-600 dark:text-gray-400">Source</label>
                            <select data-filter="source" class="ml-1 text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-700">
                                <option value="all">All Sources</option>
                            </select>
                        </div>
                        
                        <!-- Search -->
                        <div class="filter-group">
                            <label class="text-xs text-gray-600 dark:text-gray-400">Search</label>
                            <input type="text" data-filter="search" placeholder="Search logs..." 
                                   class="ml-1 text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-700 w-32">
                        </div>
                    </div>
                    
                    <!-- Action Controls -->
                    <div class="actions flex space-x-2">
                        <button data-action="pause" class="px-3 py-1 text-sm bg-yellow-600 text-white rounded-md hover:bg-yellow-700 flex items-center space-x-1">
                            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M6 4h2v12H6V4zm6 0h2v12h-2V4z"/>
                            </svg>
                            <span>Pause</span>
                        </button>
                        <button data-action="auto-scroll" class="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center space-x-1">
                            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M16 15v-1a2 2 0 00-2-2H6a2 2 0 00-2 2v1m12 0v1a2 2 0 01-2 2H6a2 2 0 01-2-2v-1m12 0H4"/>
                            </svg>
                            <span>Auto-scroll</span>
                        </button>
                        <button data-action="export" class="px-3 py-1 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center space-x-1">
                            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M4 16v1a3 3 0 003 3h6a3 3 0 003-3v-1m-4-4l-2 2m0 0l-2-2m2 2V3"/>
                            </svg>
                            <span>Export</span>
                        </button>
                        <button data-action="clear" class="px-3 py-1 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 flex items-center space-x-1">
                            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9zM4 5a2 2 0 012-2v1a1 1 0 001 1h6a1 1 0 001-1V3a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V5zM8 11a1 1 0 012 0v2a1 1 0 11-2 0v-2zm4 0a1 1 0 012 0v2a1 1 0 11-2 0v-2z" clip-rule="evenodd"/>
                            </svg>
                            <span>Clear</span>
                        </button>
                    </div>
                </div>
                
                <!-- Log Stats -->
                <div class="log-stats px-4 py-2 bg-gray-100 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                    <div class="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
                        <div class="stats-left">
                            <span class="total-logs">Total: 0 logs</span>
                            <span class="filtered-logs ml-4">Filtered: 0 logs</span>
                        </div>
                        <div class="stats-right">
                            <span class="status-indicator ${this.isPaused ? 'text-yellow-600' : 'text-green-600'}">
                                ${this.isPaused ? '⏸️ Paused' : '▶️ Live'}
                            </span>
                        </div>
                    </div>
                </div>
                
                <!-- Log Container -->
                <div class="log-container overflow-auto h-96 bg-white dark:bg-gray-800">
                    <div class="log-list">
                        <!-- Logs will be rendered here -->
                        <div class="empty-state text-center py-12 text-gray-500 dark:text-gray-400">
                            <svg class="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                            </svg>
                            <div class="text-lg font-medium mb-2">No logs yet</div>
                            <div class="text-sm">Logs will appear here as they are generated</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.updateSourceFilter();
        this.applyFilters();
    }

    updateSourceFilter() {
        const sourceSelect = this.querySelector('[data-filter="source"]');
        if (sourceSelect) {
            const sources = this.getUniqueSources();
            const currentValue = sourceSelect.value;
            
            sourceSelect.innerHTML = '<option value="all">All Sources</option>';
            sources.forEach(source => {
                const option = document.createElement('option');
                option.value = source;
                option.textContent = source;
                sourceSelect.appendChild(option);
            });
            
            sourceSelect.value = currentValue;
        }
    }

    renderLogs() {
        const container = this.querySelector('.log-list');
        const statsContainer = this.querySelector('.log-stats');
        
        // Update stats
        const totalLogs = this.logs.length;
        const filteredLogs = this.filteredLogs.length;
        
        const totalElement = statsContainer.querySelector('.total-logs');
        const filteredElement = statsContainer.querySelector('.filtered-logs');
        
        if (totalElement) totalElement.textContent = `Total: ${totalLogs} logs`;
        if (filteredElement) filteredElement.textContent = `Filtered: ${filteredLogs} logs`;
        
        // Render logs
        if (this.filteredLogs.length === 0) {
            const message = this.logs.length === 0 ? 
                'No logs yet' : 
                'No logs match current filters';
            
            container.innerHTML = `
                <div class="empty-state text-center py-12 text-gray-500 dark:text-gray-400">
                    <svg class="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                    <div class="text-lg font-medium mb-2">${message}</div>
                    <div class="text-sm">Try adjusting your filters</div>
                </div>
            `;
            return;
        }
        
        // Render log entries (with virtual scrolling for performance)
        const logsToShow = this.filteredLogs.slice(-100); // Show last 100 logs for performance
        
        container.innerHTML = logsToShow.map(log => `
            <div class="log-entry border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50" data-log-id="${log.id}">
                <div class="log-row flex items-start space-x-3 p-3">
                    <!-- Level Indicator -->
                    <div class="log-level flex-shrink-0">
                        <span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${this.getLevelColor(log.level)}">
                            ${this.getLevelIcon(log.level)} ${log.level.toUpperCase()}
                        </span>
                    </div>
                    
                    <!-- Timestamp -->
                    <div class="log-timestamp flex-shrink-0 text-xs text-gray-500 dark:text-gray-400 mt-1 min-w-[80px]">
                        ${this.formatTimestamp(log.timestamp)}
                    </div>
                    
                    <!-- Source -->
                    <div class="log-source flex-shrink-0 text-xs font-medium text-gray-600 dark:text-gray-300 mt-1 min-w-[80px]">
                        ${log.source}
                    </div>
                    
                    <!-- Message -->
                    <div class="log-message flex-1 text-sm text-gray-900 dark:text-gray-100 break-words">
                        ${this.highlightSearchTerm(log.message, this.filters.search)}
                    </div>
                </div>
            </div>
        `).join('');
        
        // Update source filter options
        this.updateSourceFilter();
    }

    // Public API methods for external use
    async loadLogs() {
        try {
            const logs = await window.dashboard.api.getLogs({ limit: 100 });
            if (logs && Array.isArray(logs)) {
                this.addLogs(logs);
            }
        } catch (error) {
            console.error('Failed to load logs:', error);
            this.renderError('Failed to load logs');
        }
    }

    // Method to simulate adding logs for testing
    simulateLog(level = 'info', source = 'test', message = 'Test log message') {
        this.addLog({
            level,
            source,
            message,
            timestamp: new Date().toISOString()
        });
    }
}

// Register the custom element
customElements.define('log-viewer', LogViewer);
/**
 * ActivityHeatmap Component
 * GitHub-style activity heatmap for displaying project activity over time
 */
class ActivityHeatmap extends HTMLElement {
    constructor() {
        super();
        this.activityData = null;
        this.refreshInterval = null;
        this.tooltip = null;
        this.componentId = null;
        this.eventListenerIds = [];
        this.cachedElements = new Map();
    }

    connectedCallback() {
        // Register component for memory management
        if (window.memoryOptimizer) {
            this.componentId = window.memoryOptimizer.registerComponent(this);
        }
        
        this.render();
        this.createTooltip();
        this.loadActivityData();
        this.setupRealtimeUpdates();
        
        // Auto-refresh every 10 minutes as fallback
        this.refreshInterval = setInterval(() => {
            if (!window.dashboard?.state?.wsConnected) {
                this.loadActivityData();
            }
        }, 600000);
    }

    disconnectedCallback() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        if (this.tooltip) {
            this.tooltip.remove();
        }
        this.cleanup();
        
        // Memory cleanup
        if (window.memoryOptimizer && this.componentId) {
            window.memoryOptimizer.cleanupComponent(this.componentId);
        }
        
        // Clean up cached elements
        this.cachedElements.clear();
    }
    
    setupRealtimeUpdates() {
        // Listen for WebSocket updates with memory management
        this.activityUpdateHandler = (event) => {
            const data = event.detail?.data || {};
            this.updateActivity(data);
        };
        
        // Use memory optimizer for managed event listeners
        if (window.memoryOptimizer) {
            const listenerId = window.memoryOptimizer.addManagedListener(
                window, 
                'activity-updated', 
                this.activityUpdateHandler
            );
            this.eventListenerIds.push(listenerId);
        } else {
            window.addEventListener('activity-updated', this.activityUpdateHandler);
        }
    }
    
    cleanup() {
        // Clean up managed event listeners
        if (window.memoryOptimizer) {
            this.eventListenerIds.forEach(id => {
                window.memoryOptimizer.removeManagedListener(id);
            });
            this.eventListenerIds = [];
        } else if (this.activityUpdateHandler) {
            window.removeEventListener('activity-updated', this.activityUpdateHandler);
        }
    }

    async loadActivityData() {
        try {
            const response = await axios.get('/web/api/activity');
            this.activityData = response.data;
            this.renderHeatmap();
        } catch (error) {
            console.error('Failed to load activity data:', error);
            this.renderError('Failed to load activity data');
        }
    }

    updateActivity(activityData) {
        if (!activityData || JSON.stringify(this.activityData) === JSON.stringify(activityData)) {
            return; // No change needed
        }
        
        const oldData = this.activityData;
        this.activityData = activityData;
        
        // Apply incremental updates with animation
        this.applyActivityUpdatesWithAnimation(oldData, activityData);
    }
    
    applyActivityUpdatesWithAnimation(oldData, newData) {
        if (!oldData || !oldData.activities || !newData || !newData.activities) {
            // No old data or major structure change - do full re-render
            this.renderHeatmap();
            return;
        }
        
        // Use WeakMap caching for performance
        const cacheKey = 'oldActivitiesMap';
        let oldActivitiesMap = window.memoryOptimizer ? 
            window.memoryOptimizer.getCache(oldData, cacheKey) : null;
            
        if (!oldActivitiesMap) {
            oldActivitiesMap = new Map(
                oldData.activities.map(a => [a.date, a.activity_count])
            );
            
            if (window.memoryOptimizer) {
                window.memoryOptimizer.cache(oldData, cacheKey, oldActivitiesMap);
            }
        }
        
        // Find changed dates
        const changedDates = [];
        newData.activities.forEach(activity => {
            const oldCount = oldActivitiesMap.get(activity.date) || 0;
            if (oldCount !== activity.activity_count) {
                changedDates.push({
                    date: activity.date,
                    oldCount,
                    newCount: activity.activity_count
                });
            }
        });
        
        // Update individual cells with animation using RAF for better performance
        if (window.requestAnimationFrame) {
            window.requestAnimationFrame(() => {
                changedDates.forEach(({ date, oldCount, newCount }) => {
                    const cell = this.querySelector(`[data-date="${date}"]`);
                    if (cell) {
                        // Add pulse animation
                        cell.style.animation = 'pulse 0.5s ease-out';
                        
                        // Batch DOM updates
                        window.requestAnimationFrame(() => {
                            // Update cell appearance
                            cell.className = cell.className.replace(/bg-\w+-\d+/g, '');
                            cell.className += ` ${this.getActivityColor(newCount)}`;
                            cell.dataset.count = newCount;
                            cell.dataset.level = this.getActivityLevel(newCount);
                        });
                    }
                });
            });
        } else {
            // Fallback for browsers without RAF
            changedDates.forEach(({ date, oldCount, newCount }) => {
                const cell = this.querySelector(`[data-date="${date}"]`);
                if (cell) {
                    cell.style.animation = 'pulse 0.5s ease-out';
                    setTimeout(() => {
                        cell.className = cell.className.replace(/bg-\w+-\d+/g, '');
                        cell.className += ` ${this.getActivityColor(newCount)}`;
                        cell.dataset.count = newCount;
                        cell.dataset.level = this.getActivityLevel(newCount);
                    }, 100);
                }
            });
        }
        
        // Update stats section
        setTimeout(() => {
            const dates = this.generateDateRange();
            const newStats = this.calculateStats(dates);
            this.updateStatsSection(newStats);
        }, 300);
        
        // If more than 10 changes, do full re-render for performance
        if (changedDates.length > 10) {
            setTimeout(() => this.renderHeatmap(), 500);
        }
    }
    
    updateStatsSection(stats) {
        // Update active days
        const activeDaysElement = this.querySelector('.stats-grid .stat-item:nth-child(1) .text-lg');
        if (activeDaysElement) {
            activeDaysElement.textContent = stats.activeDays;
        }
        
        // Update current streak
        const currentStreakElement = this.querySelector('.stats-grid .stat-item:nth-child(2) .text-lg');
        if (currentStreakElement) {
            currentStreakElement.textContent = stats.currentStreak;
        }
        
        // Update longest streak
        const longestStreakElement = this.querySelector('.stats-grid .stat-item:nth-child(3) .text-lg');
        if (longestStreakElement) {
            longestStreakElement.textContent = stats.longestStreak;
        }
        
        // Update average per day
        const avgElement = this.querySelector('.stats-grid .stat-item:nth-child(4) .text-lg');
        if (avgElement) {
            avgElement.textContent = stats.avgPerDay.toFixed(1);
        }
        
        // Update header stats
        const headerStats = this.querySelector('.heatmap-footer .stats');
        if (headerStats) {
            headerStats.textContent = `Total: ${stats.totalActivities} activities`;
        }
        
        const activityRateElement = this.querySelector('.heatmap-container + * .text-xs');
        if (activityRateElement) {
            activityRateElement.textContent = `${stats.activeDays} active days (${stats.activityRate}%)`;
        }
    }

    createTooltip() {
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'activity-tooltip fixed bg-black text-white text-xs rounded px-2 py-1 pointer-events-none z-50 opacity-0 transition-opacity duration-200';
        document.body.appendChild(this.tooltip);
    }

    getActivityColor(count) {
        if (count === 0) return 'bg-gray-100 dark:bg-gray-800';
        if (count <= 2) return 'bg-green-200 dark:bg-green-900/50';
        if (count <= 5) return 'bg-green-400 dark:bg-green-700';
        if (count <= 10) return 'bg-green-600 dark:bg-green-500';
        return 'bg-green-800 dark:bg-green-400';
    }

    getActivityLevel(count) {
        if (count === 0) return 0;
        if (count <= 2) return 1;
        if (count <= 5) return 2;
        if (count <= 10) return 3;
        return 4;
    }

    formatDate(date) {
        return new Date(date).toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    generateDateRange() {
        const dates = [];
        const end = new Date();
        const start = new Date();
        start.setDate(end.getDate() - 364); // 365 days total
        
        // Start from the beginning of the week
        const startDayOfWeek = start.getDay();
        start.setDate(start.getDate() - startDayOfWeek);

        const current = new Date(start);
        while (current <= end) {
            dates.push(new Date(current));
            current.setDate(current.getDate() + 1);
        }

        return dates;
    }

    getWeeksArray(dates) {
        const weeks = [];
        let currentWeek = [];

        dates.forEach(date => {
            if (currentWeek.length === 7) {
                weeks.push(currentWeek);
                currentWeek = [];
            }
            currentWeek.push(date);
        });

        if (currentWeek.length > 0) {
            weeks.push(currentWeek);
        }

        return weeks;
    }

    getMonthLabels(weeks) {
        const months = [];
        let lastMonth = -1;

        weeks.forEach((week, weekIndex) => {
            const firstDay = week[0];
            const month = firstDay.getMonth();
            
            if (month !== lastMonth && weekIndex > 0) {
                months.push({
                    name: firstDay.toLocaleDateString('en-US', { month: 'short' }),
                    weekIndex: weekIndex
                });
            }
            lastMonth = month;
        });

        return months;
    }

    getActivityForDate(date) {
        if (!this.activityData || !this.activityData.activities) {
            return 0;
        }

        const dateStr = date.toISOString().split('T')[0];
        const activity = this.activityData.activities.find(a => a.date === dateStr);
        return activity ? activity.activity_count : 0;
    }

    render() {
        this.innerHTML = `
            <div class="activity-heatmap">
                <!-- Loading state -->
                <div class="loading text-center py-8">
                    <svg class="animate-spin h-8 w-8 mx-auto mb-2 text-gray-400" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <div class="text-gray-500 dark:text-gray-400">Loading activity data...</div>
                </div>
            </div>
        `;
    }

    renderHeatmap() {
        if (!this.activityData) {
            this.renderError('No activity data available');
            return;
        }

        const dates = this.generateDateRange();
        const weeks = this.getWeeksArray(dates);
        const monthLabels = this.getMonthLabels(weeks);
        const stats = this.calculateStats(dates);

        this.innerHTML = `
            <div class="activity-heatmap space-y-4">
                <!-- Header -->
                <div class="flex items-center justify-between">
                    <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300">
                        Activity in the last year
                    </h4>
                    <div class="text-xs text-gray-500 dark:text-gray-400">
                        ${stats.activeDays} active days (${stats.activityRate}%)
                    </div>
                </div>

                <!-- Heatmap Container -->
                <div class="heatmap-container">
                    <!-- Month Labels -->
                    <div class="month-labels flex mb-1" style="margin-left: 30px;">
                        ${monthLabels.map(month => `
                            <div class="month-label text-xs text-gray-500 dark:text-gray-400" 
                                 style="width: ${14 * month.weekIndex + 14}px; position: absolute; left: ${14 * month.weekIndex}px;">
                                ${month.name}
                            </div>
                        `).join('')}
                    </div>

                    <!-- Main Grid -->
                    <div class="heatmap-grid flex">
                        <!-- Day Labels -->
                        <div class="day-labels flex flex-col mr-2">
                            ${['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day, index) => `
                                <div class="day-label text-xs text-gray-500 dark:text-gray-400 h-3 flex items-center ${index % 2 === 0 ? '' : 'invisible'}">
                                    ${day}
                                </div>
                            `).join('')}
                        </div>

                        <!-- Activity Grid -->
                        <div class="activity-grid flex">
                            ${weeks.map(week => `
                                <div class="week flex flex-col mr-1">
                                    ${week.map(date => {
                                        const activityCount = this.getActivityForDate(date);
                                        const isToday = this.isToday(date);
                                        return `
                                            <div class="activity-cell w-3 h-3 mb-1 rounded-sm cursor-pointer border ${isToday ? 'border-gray-400 dark:border-gray-500' : 'border-transparent'} ${this.getActivityColor(activityCount)}"
                                                 data-date="${date.toISOString().split('T')[0]}"
                                                 data-count="${activityCount}"
                                                 data-level="${this.getActivityLevel(activityCount)}"
                                                 onmouseenter="this.closest('activity-heatmap').showTooltip(event, '${this.formatDate(date)}', ${activityCount})"
                                                 onmouseleave="this.closest('activity-heatmap').hideTooltip()">
                                            </div>
                                        `;
                                    }).join('')}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <!-- Legend and Stats -->
                <div class="heatmap-footer flex items-center justify-between">
                    <div class="legend flex items-center space-x-2">
                        <span class="text-xs text-gray-500 dark:text-gray-400">Less</span>
                        <div class="legend-scale flex space-x-1">
                            ${[0, 1, 2, 3, 4].map(level => `
                                <div class="w-3 h-3 rounded-sm ${this.getActivityColorByLevel(level)}"></div>
                            `).join('')}
                        </div>
                        <span class="text-xs text-gray-500 dark:text-gray-400">More</span>
                    </div>
                    
                    <div class="stats text-xs text-gray-500 dark:text-gray-400">
                        Total: ${stats.totalActivities} activities
                    </div>
                </div>

                <!-- Additional Stats -->
                <div class="stats-grid grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                    <div class="stat-item text-center">
                        <div class="text-lg font-semibold text-gray-900 dark:text-white">${stats.activeDays}</div>
                        <div class="text-xs text-gray-500 dark:text-gray-400">Active Days</div>
                    </div>
                    <div class="stat-item text-center">
                        <div class="text-lg font-semibold text-gray-900 dark:text-white">${stats.currentStreak}</div>
                        <div class="text-xs text-gray-500 dark:text-gray-400">Current Streak</div>
                    </div>
                    <div class="stat-item text-center">
                        <div class="text-lg font-semibold text-gray-900 dark:text-white">${stats.longestStreak}</div>
                        <div class="text-xs text-gray-500 dark:text-gray-400">Longest Streak</div>
                    </div>
                    <div class="stat-item text-center">
                        <div class="text-lg font-semibold text-gray-900 dark:text-white">${stats.avgPerDay.toFixed(1)}</div>
                        <div class="text-xs text-gray-500 dark:text-gray-400">Avg/Day</div>
                    </div>
                </div>
            </div>
        `;
    }

    getActivityColorByLevel(level) {
        const colors = [
            'bg-gray-100 dark:bg-gray-800',
            'bg-green-200 dark:bg-green-900/50',
            'bg-green-400 dark:bg-green-700',
            'bg-green-600 dark:bg-green-500',
            'bg-green-800 dark:bg-green-400'
        ];
        return colors[level] || colors[0];
    }

    isToday(date) {
        const today = new Date();
        return date.toDateString() === today.toDateString();
    }

    calculateStats(dates) {
        let totalActivities = 0;
        let activeDays = 0;
        let currentStreak = 0;
        let longestStreak = 0;
        let tempStreak = 0;

        // Calculate from most recent date backwards
        const sortedDates = [...dates].reverse();
        
        sortedDates.forEach((date, index) => {
            const count = this.getActivityForDate(date);
            totalActivities += count;
            
            if (count > 0) {
                activeDays++;
                tempStreak++;
                
                // Update current streak (only for consecutive days from today)
                if (index === 0 || (currentStreak > 0 && count > 0)) {
                    currentStreak = tempStreak;
                }
            } else {
                longestStreak = Math.max(longestStreak, tempStreak);
                if (index < currentStreak) {
                    currentStreak = 0;
                }
                tempStreak = 0;
            }
        });
        
        longestStreak = Math.max(longestStreak, tempStreak);
        
        return {
            totalActivities,
            activeDays,
            activityRate: Math.round((activeDays / dates.length) * 100),
            currentStreak,
            longestStreak,
            avgPerDay: totalActivities / dates.length
        };
    }

    showTooltip(event, date, count) {
        if (!this.tooltip) return;

        const activityText = count === 0 ? 'No activity' : 
                           count === 1 ? '1 activity' : 
                           `${count} activities`;

        this.tooltip.innerHTML = `
            <div>${activityText}</div>
            <div class="text-gray-300">${date}</div>
        `;

        this.tooltip.style.left = `${event.pageX + 10}px`;
        this.tooltip.style.top = `${event.pageY - 10}px`;
        this.tooltip.style.opacity = '1';
    }

    hideTooltip() {
        if (this.tooltip) {
            this.tooltip.style.opacity = '0';
        }
    }

    renderError(message) {
        this.innerHTML = `
            <div class="activity-heatmap-error text-center py-8">
                <svg class="w-12 h-12 mx-auto mb-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">Unable to Load Activity Data</h3>
                <p class="text-gray-500 dark:text-gray-400">${message}</p>
                <button 
                    onclick="this.closest('activity-heatmap').loadActivityData()"
                    class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                    Retry
                </button>
            </div>
        `;
    }
}

// Register the custom element
customElements.define('activity-heatmap', ActivityHeatmap);
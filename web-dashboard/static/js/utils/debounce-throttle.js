/**
 * Enhanced Debouncing and Throttling Utilities
 * Optimized performance utilities for WebSocket updates and UI interactions
 */

class PerformanceOptimizer {
    constructor() {
        this.activeThrottles = new Map();
        this.activeDebounces = new Map();
        this.batchQueue = new Map();
        this.renderScheduled = false;
        
        // Performance monitoring
        this.stats = {
            debounced_calls: 0,
            throttled_calls: 0,
            batched_events: 0,
            renders_prevented: 0
        };
    }

    /**
     * Enhanced debounce with immediate execution option
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @param {Object} options - Options (immediate, maxWait)
     * @returns {Function} Debounced function
     */
    debounce(func, wait, options = {}) {
        const { immediate = false, maxWait = null } = options;
        let timeoutId;
        let maxTimeoutId;
        let lastCallTime = 0;
        let lastExecTime = 0;
        
        const debounced = (...args) => {
            const now = Date.now();
            lastCallTime = now;
            
            this.stats.debounced_calls++;
            
            const callNow = immediate && !timeoutId;
            
            // Clear existing timeout
            if (timeoutId) {
                clearTimeout(timeoutId);
            }
            
            // Set new timeout
            timeoutId = setTimeout(() => {
                timeoutId = null;
                if (!immediate) {
                    lastExecTime = Date.now();
                    func.apply(this, args);
                }
            }, wait);
            
            // Handle maxWait
            if (maxWait && !maxTimeoutId) {
                maxTimeoutId = setTimeout(() => {
                    maxTimeoutId = null;
                    if (timeoutId) {
                        clearTimeout(timeoutId);
                        timeoutId = null;
                    }
                    lastExecTime = Date.now();
                    func.apply(this, args);
                }, maxWait);
            }
            
            // Immediate execution
            if (callNow) {
                lastExecTime = now;
                func.apply(this, args);
            }
        };
        
        // Add cancel method
        debounced.cancel = () => {
            if (timeoutId) {
                clearTimeout(timeoutId);
                timeoutId = null;
            }
            if (maxTimeoutId) {
                clearTimeout(maxTimeoutId);
                maxTimeoutId = null;
            }
        };
        
        // Add flush method (execute immediately)
        debounced.flush = (...args) => {
            debounced.cancel();
            lastExecTime = Date.now();
            return func.apply(this, args);
        };
        
        return debounced;
    }

    /**
     * Enhanced throttle with leading and trailing options
     * @param {Function} func - Function to throttle
     * @param {number} limit - Throttle limit in milliseconds
     * @param {Object} options - Options (leading, trailing)
     * @returns {Function} Throttled function
     */
    throttle(func, limit, options = {}) {
        const { leading = true, trailing = true } = options;
        let inThrottle = false;
        let lastResult;
        let lastArgs;
        let timeoutId;
        
        const throttled = (...args) => {
            this.stats.throttled_calls++;
            lastArgs = args;
            
            if (!inThrottle) {
                // Leading execution
                if (leading) {
                    lastResult = func.apply(this, args);
                }
                
                inThrottle = true;
                
                // Set up trailing execution
                if (trailing) {
                    timeoutId = setTimeout(() => {
                        inThrottle = false;
                        if (lastArgs) {
                            lastResult = func.apply(this, lastArgs);
                            lastArgs = null;
                        }
                    }, limit);
                } else {
                    setTimeout(() => {
                        inThrottle = false;
                    }, limit);
                }
            }
            
            return lastResult;
        };
        
        // Add cancel method
        throttled.cancel = () => {
            if (timeoutId) {
                clearTimeout(timeoutId);
                timeoutId = null;
            }
            inThrottle = false;
            lastArgs = null;
        };
        
        return throttled;
    }

    /**
     * Batch similar events and process them together
     * @param {string} batchKey - Unique key for the batch
     * @param {Function} processor - Function to process the batch
     * @param {number} delay - Batch delay in milliseconds
     */
    batchEvents(batchKey, processor, delay = 50) {
        if (!this.batchQueue.has(batchKey)) {
            this.batchQueue.set(batchKey, {
                items: [],
                timeoutId: null,
                processor
            });
        }
        
        const batch = this.batchQueue.get(batchKey);
        
        return (data) => {
            this.stats.batched_events++;
            batch.items.push({
                data,
                timestamp: Date.now()
            });
            
            // Clear existing timeout
            if (batch.timeoutId) {
                clearTimeout(batch.timeoutId);
            }
            
            // Set new timeout
            batch.timeoutId = setTimeout(() => {
                const items = batch.items.slice(); // Copy items
                batch.items.length = 0; // Clear original array
                batch.timeoutId = null;
                
                try {
                    processor(items);
                } catch (error) {
                    console.error(`Error processing batch ${batchKey}:`, error);
                }
            }, delay);
        };
    }

    /**
     * Request animation frame throttling for rendering
     * @param {Function} renderFunc - Render function
     * @returns {Function} RAF-throttled function
     */
    throttleRender(renderFunc) {
        let rafId = null;
        let lastArgs = null;
        
        return (...args) => {
            lastArgs = args;
            
            if (rafId === null) {
                rafId = requestAnimationFrame(() => {
                    rafId = null;
                    try {
                        renderFunc.apply(this, lastArgs);
                    } catch (error) {
                        console.error('Render error:', error);
                    }
                });
            } else {
                this.stats.renders_prevented++;
            }
        };
    }

    /**
     * Create a smart updater that combines debouncing and batching
     * @param {Function} updateFunc - Update function
     * @param {Object} options - Configuration options
     */
    createSmartUpdater(updateFunc, options = {}) {
        const {
            debounceTime = 100,
            throttleTime = 50,
            batchKey = 'default',
            maxBatchSize = 10,
            strategy = 'debounce' // 'debounce', 'throttle', 'batch', 'hybrid'
        } = options;
        
        switch (strategy) {
            case 'throttle':
                return this.throttle(updateFunc, throttleTime);
                
            case 'batch':
                return this.batchEvents(batchKey, (items) => {
                    // Process only the latest items if batch is too large
                    const processItems = items.length > maxBatchSize ? 
                        items.slice(-maxBatchSize) : items;
                    updateFunc(processItems);
                }, debounceTime);
                
            case 'hybrid':
                // Combine throttling and batching
                const batchedUpdater = this.batchEvents(batchKey, updateFunc, debounceTime);
                return this.throttle(batchedUpdater, throttleTime);
                
            case 'debounce':
            default:
                return this.debounce(updateFunc, debounceTime, { maxWait: debounceTime * 3 });
        }
    }

    /**
     * Optimize WebSocket message handling
     * @param {Function} messageHandler - Message handler function
     * @param {string} messageType - Type of message
     */
    optimizeWebSocketHandler(messageHandler, messageType) {
        const options = this.getOptimizationOptions(messageType);
        return this.createSmartUpdater(messageHandler, options);
    }

    /**
     * Get optimization options based on message type
     * @param {string} messageType - Type of message
     */
    getOptimizationOptions(messageType) {
        const configs = {
            'session_update': {
                strategy: 'hybrid',
                debounceTime: 200,
                throttleTime: 100,
                batchKey: 'sessions',
                maxBatchSize: 5
            },
            'health_update': {
                strategy: 'debounce',
                debounceTime: 500,
                maxBatchSize: 3
            },
            'activity_update': {
                strategy: 'throttle',
                throttleTime: 1000
            },
            'log_update': {
                strategy: 'batch',
                debounceTime: 100,
                batchKey: 'logs',
                maxBatchSize: 20
            },
            'render': {
                strategy: 'throttle',
                throttleTime: 16 // ~60fps
            },
            'scroll': {
                strategy: 'throttle',
                throttleTime: 16
            },
            'resize': {
                strategy: 'debounce',
                debounceTime: 150
            },
            'input': {
                strategy: 'debounce',
                debounceTime: 300
            }
        };
        
        return configs[messageType] || {
            strategy: 'debounce',
            debounceTime: 200
        };
    }

    /**
     * Get performance statistics
     */
    getStats() {
        return {
            ...this.stats,
            active_throttles: this.activeThrottles.size,
            active_debounces: this.activeDebounces.size,
            batch_queues: this.batchQueue.size,
            memory_usage: this.getMemoryUsage()
        };
    }

    /**
     * Estimate memory usage
     */
    getMemoryUsage() {
        let totalItems = 0;
        this.batchQueue.forEach(batch => {
            totalItems += batch.items.length;
        });
        
        return {
            batch_queue_items: totalItems,
            estimated_kb: Math.round(totalItems * 0.1) // Rough estimate
        };
    }

    /**
     * Clear all optimizations
     */
    clear() {
        // Clear batch queues
        this.batchQueue.forEach(batch => {
            if (batch.timeoutId) {
                clearTimeout(batch.timeoutId);
            }
        });
        this.batchQueue.clear();
        
        // Reset stats
        this.stats = {
            debounced_calls: 0,
            throttled_calls: 0,
            batched_events: 0,
            renders_prevented: 0
        };
    }

    /**
     * Create performance-optimized event listener
     * @param {Element} element - Element to attach listener to
     * @param {string} event - Event type
     * @param {Function} handler - Event handler
     * @param {Object} options - Optimization options
     */
    addOptimizedListener(element, event, handler, options = {}) {
        const optimizedHandler = this.createSmartUpdater(handler, {
            ...this.getOptimizationOptions(event),
            ...options
        });
        
        element.addEventListener(event, optimizedHandler, options.listenerOptions);
        
        return () => {
            element.removeEventListener(event, optimizedHandler, options.listenerOptions);
            if (optimizedHandler.cancel) {
                optimizedHandler.cancel();
            }
        };
    }
}

// Create global instance
const performanceOptimizer = new PerformanceOptimizer();

// Export utilities
window.performanceOptimizer = performanceOptimizer;

// Legacy compatibility - extend dashboard utils
if (window.dashboard && window.dashboard.utils) {
    // Enhanced versions with performance monitoring
    window.dashboard.utils.debounce = (func, wait, options) => 
        performanceOptimizer.debounce(func, wait, options);
        
    window.dashboard.utils.throttle = (func, limit, options) => 
        performanceOptimizer.throttle(func, limit, options);
        
    window.dashboard.utils.batchEvents = (key, processor, delay) => 
        performanceOptimizer.batchEvents(key, processor, delay);
        
    window.dashboard.utils.optimizeHandler = (handler, type) => 
        performanceOptimizer.optimizeWebSocketHandler(handler, type);
        
    window.dashboard.utils.throttleRender = (renderFunc) => 
        performanceOptimizer.throttleRender(renderFunc);
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PerformanceOptimizer, performanceOptimizer };
}
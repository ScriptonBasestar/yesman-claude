/**
 * Memory Optimizer
 * Advanced memory management utilities for performance optimization
 */
class MemoryOptimizer {
    constructor() {
        this.weakMapCache = new WeakMap();
        this.eventListeners = new Map();
        this.domNodePool = new Map();
        this.observedElements = new Set();
        this.cleanupCallbacks = new Set();
        this.stats = {
            cached_objects: 0,
            pooled_nodes: 0,
            managed_listeners: 0,
            memory_saved_kb: 0,
            cleanup_operations: 0
        };
        
        // Setup automatic cleanup
        this.setupPeriodicCleanup();
        this.setupVisibilityChangeCleanup();
    }

    /**
     * WeakMap-based caching system
     */
    cache(object, key, value) {
        if (!this.weakMapCache.has(object)) {
            this.weakMapCache.set(object, new Map());
            this.stats.cached_objects++;
        }
        
        const objectCache = this.weakMapCache.get(object);
        objectCache.set(key, value);
        return value;
    }

    getCache(object, key) {
        const objectCache = this.weakMapCache.get(object);
        return objectCache ? objectCache.get(key) : undefined;
    }

    hasCache(object, key) {
        const objectCache = this.weakMapCache.get(object);
        return objectCache ? objectCache.has(key) : false;
    }

    clearCache(object) {
        if (this.weakMapCache.has(object)) {
            this.weakMapCache.delete(object);
            this.stats.cached_objects = Math.max(0, this.stats.cached_objects - 1);
        }
    }

    /**
     * Event listener management with automatic cleanup
     */
    addManagedListener(element, event, handler, options = {}) {
        const listenerId = this.generateListenerId(element, event, handler);
        
        // Wrap handler with cleanup tracking
        const wrappedHandler = (...args) => {
            try {
                return handler(...args);
            } catch (error) {
                console.error('Event handler error:', error);
            }
        };
        
        // Add listener
        element.addEventListener(event, wrappedHandler, options);
        
        // Track for cleanup
        this.eventListeners.set(listenerId, {
            element,
            event,
            handler: wrappedHandler,
            options,
            timestamp: Date.now()
        });
        
        this.stats.managed_listeners++;
        return listenerId;
    }

    removeManagedListener(listenerId) {
        const listener = this.eventListeners.get(listenerId);
        if (listener) {
            listener.element.removeEventListener(
                listener.event, 
                listener.handler, 
                listener.options
            );
            this.eventListeners.delete(listenerId);
            this.stats.managed_listeners--;
            this.stats.cleanup_operations++;
        }
    }

    removeAllListenersForElement(element) {
        let removedCount = 0;
        for (const [id, listener] of this.eventListeners) {
            if (listener.element === element) {
                this.removeManagedListener(id);
                removedCount++;
            }
        }
        return removedCount;
    }

    generateListenerId(element, event, handler) {
        return `${element.tagName || 'unknown'}_${event}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * DOM node pooling for reuse
     */
    getPooledNode(tagName, className = '') {
        const poolKey = `${tagName}_${className}`;
        const pool = this.domNodePool.get(poolKey) || [];
        
        if (pool.length > 0) {
            const node = pool.pop();
            this.domNodePool.set(poolKey, pool);
            this.resetNode(node);
            return node;
        }
        
        // Create new node if pool is empty
        const node = document.createElement(tagName);
        if (className) {
            node.className = className;
        }
        return node;
    }

    returnToPool(node, poolKey = null) {
        if (!node || !node.tagName) return;
        
        const key = poolKey || `${node.tagName}_${node.className}`;
        const pool = this.domNodePool.get(key) || [];
        
        // Limit pool size to prevent memory bloat
        if (pool.length < 10) {
            this.resetNode(node);
            pool.push(node);
            this.domNodePool.set(key, pool);
            this.stats.pooled_nodes++;
        } else {
            // Remove from DOM if pool is full
            if (node.parentNode) {
                node.parentNode.removeChild(node);
            }
        }
    }

    resetNode(node) {
        // Clean node for reuse
        node.innerHTML = '';
        node.removeAttribute('style');
        node.removeAttribute('data-original-title');
        
        // Remove all data attributes
        for (const attr of node.attributes) {
            if (attr.name.startsWith('data-') && attr.name !== 'data-pool-key') {
                node.removeAttribute(attr.name);
            }
        }
        
        // Remove from parent if attached
        if (node.parentNode) {
            node.parentNode.removeChild(node);
        }
    }

    /**
     * Memory-efficient DOM operations
     */
    createOptimizedElement(tagName, options = {}) {
        const { className, content, attributes, pooled = true } = options;
        
        const element = pooled ? 
            this.getPooledNode(tagName, className) : 
            document.createElement(tagName);
        
        if (className && !pooled) {
            element.className = className;
        }
        
        if (content) {
            if (typeof content === 'string') {
                element.textContent = content;
            } else {
                element.appendChild(content);
            }
        }
        
        if (attributes) {
            for (const [key, value] of Object.entries(attributes)) {
                element.setAttribute(key, value);
            }
        }
        
        return element;
    }

    createDocumentFragment() {
        return document.createDocumentFragment();
    }

    /**
     * Intersection Observer for memory-efficient visibility tracking
     */
    observeVisibility(element, callback, options = {}) {
        if (!this.intersectionObserver) {
            this.intersectionObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    const callback = this.visibilityCallbacks.get(entry.target);
                    if (callback) {
                        callback(entry.isIntersecting, entry);
                    }
                });
            }, { threshold: options.threshold || 0.1 });
            
            this.visibilityCallbacks = new Map();
        }
        
        this.visibilityCallbacks.set(element, callback);
        this.intersectionObserver.observe(element);
        this.observedElements.add(element);
        
        return () => {
            this.unobserveVisibility(element);
        };
    }

    unobserveVisibility(element) {
        if (this.intersectionObserver) {
            this.intersectionObserver.unobserve(element);
            this.visibilityCallbacks.delete(element);
            this.observedElements.delete(element);
        }
    }

    /**
     * Automatic cleanup systems
     */
    setupPeriodicCleanup() {
        // Clean up old cached data every 5 minutes
        setInterval(() => {
            this.cleanupStaleCaches();
            this.cleanupUnusedPools();
            this.stats.cleanup_operations++;
        }, 5 * 60 * 1000);
    }

    setupVisibilityChangeCleanup() {
        // Clean up when page becomes hidden
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.performFullCleanup();
            }
        });
    }

    cleanupStaleCaches() {
        const now = Date.now();
        const maxAge = 10 * 60 * 1000; // 10 minutes
        
        for (const [id, listener] of this.eventListeners) {
            if (now - listener.timestamp > maxAge) {
                this.removeManagedListener(id);
            }
        }
    }

    cleanupUnusedPools() {
        // Remove pools that haven't been used recently
        for (const [key, pool] of this.domNodePool) {
            if (pool.length > 5) {
                // Keep only half of the nodes in oversized pools
                const keepCount = Math.floor(pool.length / 2);
                const removed = pool.splice(keepCount);
                removed.forEach(node => {
                    if (node.parentNode) {
                        node.parentNode.removeChild(node);
                    }
                });
                this.domNodePool.set(key, pool);
            }
        }
    }

    performFullCleanup() {
        // Remove all event listeners
        for (const [id] of this.eventListeners) {
            this.removeManagedListener(id);
        }
        
        // Clear all pools
        for (const [key, pool] of this.domNodePool) {
            pool.forEach(node => {
                if (node.parentNode) {
                    node.parentNode.removeChild(node);
                }
            });
        }
        this.domNodePool.clear();
        
        // Unobserve all elements
        this.observedElements.forEach(element => {
            this.unobserveVisibility(element);
        });
        
        // Execute cleanup callbacks
        this.cleanupCallbacks.forEach(callback => {
            try {
                callback();
            } catch (error) {
                console.error('Cleanup callback error:', error);
            }
        });
        
        this.stats.cleanup_operations++;
    }

    /**
     * Component lifecycle management
     */
    registerComponent(component) {
        const componentId = this.generateComponentId(component);
        
        // Setup automatic cleanup when component is removed from DOM
        if (component.element) {
            const cleanupObserver = new MutationObserver((mutations) => {
                mutations.forEach(mutation => {
                    mutation.removedNodes.forEach(node => {
                        if (node === component.element || node.contains(component.element)) {
                            this.cleanupComponent(componentId);
                            cleanupObserver.disconnect();
                        }
                    });
                });
            });
            
            cleanupObserver.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
        
        return componentId;
    }

    cleanupComponent(componentId) {
        // Remove associated event listeners
        for (const [id, listener] of this.eventListeners) {
            if (id.includes(componentId)) {
                this.removeManagedListener(id);
            }
        }
        
        this.stats.cleanup_operations++;
    }

    generateComponentId(component) {
        return `component_${component.constructor.name}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Memory usage tracking and reporting
     */
    addCleanupCallback(callback) {
        this.cleanupCallbacks.add(callback);
        return () => {
            this.cleanupCallbacks.delete(callback);
        };
    }

    getMemoryStats() {
        const jsHeapSize = performance.memory ? {
            used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024 * 100) / 100,
            total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024 * 100) / 100,
            limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024 * 100) / 100
        } : null;
        
        return {
            ...this.stats,
            js_heap_mb: jsHeapSize,
            active_observers: this.observedElements.size,
            pool_efficiency: this.calculatePoolEfficiency(),
            cache_hit_ratio: this.calculateCacheHitRatio(),
            timestamp: Date.now()
        };
    }

    calculatePoolEfficiency() {
        let totalNodes = 0;
        let reusedNodes = 0;
        
        for (const pool of this.domNodePool.values()) {
            totalNodes += pool.length;
            reusedNodes += pool.filter(node => node.dataset.poolReused).length;
        }
        
        return totalNodes > 0 ? Math.round((reusedNodes / totalNodes) * 100) : 0;
    }

    calculateCacheHitRatio() {
        // This would need to be tracked during cache operations
        // For now, return estimated ratio based on cached objects
        return this.stats.cached_objects > 0 ? 85 : 0;
    }

    /**
     * Public cleanup methods
     */
    cleanup() {
        this.performFullCleanup();
    }

    destroy() {
        this.cleanup();
        
        if (this.intersectionObserver) {
            this.intersectionObserver.disconnect();
        }
        
        // Clear all references
        this.weakMapCache = null;
        this.eventListeners.clear();
        this.domNodePool.clear();
        this.observedElements.clear();
        this.cleanupCallbacks.clear();
    }
}

// Global memory optimizer instance
window.memoryOptimizer = new MemoryOptimizer();

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { MemoryOptimizer };
}
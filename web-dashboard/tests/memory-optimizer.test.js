/**
 * Tests for Memory Optimizer
 */

describe('Memory Optimizer', () => {
    let memoryOptimizer;
    
    beforeEach(() => {
        // Mock browser environment
        global.document = {
            createElement: jest.fn(tagName => ({
                tagName: tagName.toUpperCase(),
                className: '',
                innerHTML: '',
                textContent: '',
                setAttribute: jest.fn(),
                removeAttribute: jest.fn(),
                parentNode: null,
                attributes: [],
                addEventListener: jest.fn(),
                removeEventListener: jest.fn()
            })),
            createDocumentFragment: jest.fn(() => ({
                appendChild: jest.fn()
            })),
            body: {
                appendChild: jest.fn(),
                removeChild: jest.fn()
            },
            addEventListener: jest.fn(),
            removeEventListener: jest.fn(),
            hidden: false
        };
        
        global.IntersectionObserver = jest.fn(() => ({
            observe: jest.fn(),
            unobserve: jest.fn(),
            disconnect: jest.fn()
        }));
        
        global.MutationObserver = jest.fn(() => ({
            observe: jest.fn(),
            disconnect: jest.fn()
        }));
        
        global.performance = {
            memory: {
                usedJSHeapSize: 1024 * 1024 * 10, // 10MB
                totalJSHeapSize: 1024 * 1024 * 50, // 50MB
                jsHeapSizeLimit: 1024 * 1024 * 100 // 100MB
            }
        };
        
        global.localStorage = {
            getItem: jest.fn(),
            setItem: jest.fn()
        };
        
        // Import and create new instance
        const { MemoryOptimizer } = require('../static/js/utils/memory-optimizer.js');
        memoryOptimizer = new MemoryOptimizer();
    });

    describe('WeakMap caching', () => {
        it('should cache objects using WeakMap', () => {
            const testObject = { id: 1 };
            const value = 'cached_value';
            
            memoryOptimizer.cache(testObject, 'key1', value);
            
            expect(memoryOptimizer.getCache(testObject, 'key1')).toBe(value);
            expect(memoryOptimizer.hasCache(testObject, 'key1')).toBe(true);
        });
        
        it('should clear cache for specific objects', () => {
            const testObject = { id: 1 };
            memoryOptimizer.cache(testObject, 'key1', 'value1');
            
            memoryOptimizer.clearCache(testObject);
            
            expect(memoryOptimizer.getCache(testObject, 'key1')).toBeUndefined();
            expect(memoryOptimizer.hasCache(testObject, 'key1')).toBe(false);
        });
        
        it('should handle multiple keys per object', () => {
            const testObject = { id: 1 };
            
            memoryOptimizer.cache(testObject, 'key1', 'value1');
            memoryOptimizer.cache(testObject, 'key2', 'value2');
            
            expect(memoryOptimizer.getCache(testObject, 'key1')).toBe('value1');
            expect(memoryOptimizer.getCache(testObject, 'key2')).toBe('value2');
        });
    });

    describe('Event listener management', () => {
        it('should add and track managed listeners', () => {
            const element = document.createElement('div');
            const handler = jest.fn();
            
            const listenerId = memoryOptimizer.addManagedListener(element, 'click', handler);
            
            expect(typeof listenerId).toBe('string');
            expect(memoryOptimizer.stats.managed_listeners).toBe(1);
            expect(element.addEventListener).toHaveBeenCalledWith('click', expect.any(Function), {});
        });
        
        it('should remove managed listeners', () => {
            const element = document.createElement('div');
            const handler = jest.fn();
            
            const listenerId = memoryOptimizer.addManagedListener(element, 'click', handler);
            memoryOptimizer.removeManagedListener(listenerId);
            
            expect(memoryOptimizer.stats.managed_listeners).toBe(0);
            expect(memoryOptimizer.stats.cleanup_operations).toBe(1);
        });
        
        it('should remove all listeners for an element', () => {
            const element = document.createElement('div');
            
            memoryOptimizer.addManagedListener(element, 'click', jest.fn());
            memoryOptimizer.addManagedListener(element, 'mouseover', jest.fn());
            
            const removedCount = memoryOptimizer.removeAllListenersForElement(element);
            
            expect(removedCount).toBe(2);
            expect(memoryOptimizer.stats.managed_listeners).toBe(0);
        });
    });

    describe('DOM node pooling', () => {
        it('should create and pool DOM nodes', () => {
            const node1 = memoryOptimizer.getPooledNode('div', 'test-class');
            const node2 = memoryOptimizer.getPooledNode('div', 'test-class');
            
            expect(node1.tagName).toBe('DIV');
            expect(node2.tagName).toBe('DIV');
            expect(document.createElement).toHaveBeenCalledTimes(2);
        });
        
        it('should reuse nodes from pool', () => {
            const node = memoryOptimizer.getPooledNode('div', 'test-class');
            memoryOptimizer.returnToPool(node);
            
            const reusedNode = memoryOptimizer.getPooledNode('div', 'test-class');
            
            expect(reusedNode).toBe(node);
            expect(memoryOptimizer.stats.pooled_nodes).toBe(1);
        });
        
        it('should reset nodes when returning to pool', () => {
            const node = memoryOptimizer.getPooledNode('div');
            node.innerHTML = '<span>test</span>';
            node.setAttribute('style', 'color: red');
            
            memoryOptimizer.returnToPool(node);
            
            expect(node.innerHTML).toBe('');
        });
        
        it('should limit pool size', () => {
            const nodes = [];
            // Create more than 10 nodes to test pool limit
            for (let i = 0; i < 15; i++) {
                const node = memoryOptimizer.getPooledNode('div', 'test');
                nodes.push(node);
            }
            
            // Return all nodes to pool
            nodes.forEach(node => memoryOptimizer.returnToPool(node));
            
            // Pool should be limited to 10 nodes
            expect(memoryOptimizer.stats.pooled_nodes).toBeLessThanOrEqual(10);
        });
    });

    describe('Optimized element creation', () => {
        it('should create elements with options', () => {
            const element = memoryOptimizer.createOptimizedElement('span', {
                className: 'test-class',
                content: 'test content',
                attributes: { 'data-id': '123' },
                pooled: false
            });
            
            expect(element.tagName).toBe('SPAN');
            expect(element.className).toBe('test-class');
            expect(element.textContent).toBe('test content');
            expect(element.setAttribute).toHaveBeenCalledWith('data-id', '123');
        });
        
        it('should create document fragments', () => {
            const fragment = memoryOptimizer.createDocumentFragment();
            
            expect(document.createDocumentFragment).toHaveBeenCalled();
            expect(fragment).toBeDefined();
        });
    });

    describe('Visibility observation', () => {
        it('should setup intersection observer', () => {
            const element = document.createElement('div');
            const callback = jest.fn();
            
            const unobserve = memoryOptimizer.observeVisibility(element, callback);
            
            expect(typeof unobserve).toBe('function');
            expect(memoryOptimizer.observedElements.has(element)).toBe(true);
        });
        
        it('should unobserve elements', () => {
            const element = document.createElement('div');
            const callback = jest.fn();
            
            memoryOptimizer.observeVisibility(element, callback);
            memoryOptimizer.unobserveVisibility(element);
            
            expect(memoryOptimizer.observedElements.has(element)).toBe(false);
        });
    });

    describe('Component lifecycle management', () => {
        it('should register components', () => {
            const component = {
                constructor: { name: 'TestComponent' },
                element: document.createElement('div')
            };
            
            const componentId = memoryOptimizer.registerComponent(component);
            
            expect(typeof componentId).toBe('string');
            expect(componentId).toContain('TestComponent');
        });
        
        it('should cleanup components', () => {
            const component = {
                constructor: { name: 'TestComponent' },
                element: document.createElement('div')
            };
            
            const componentId = memoryOptimizer.registerComponent(component);
            memoryOptimizer.cleanupComponent(componentId);
            
            expect(memoryOptimizer.stats.cleanup_operations).toBeGreaterThan(0);
        });
    });

    describe('Memory statistics', () => {
        it('should track memory statistics', () => {
            // Perform some operations
            memoryOptimizer.cache({ id: 1 }, 'key', 'value');
            memoryOptimizer.addManagedListener(document.createElement('div'), 'click', jest.fn());
            memoryOptimizer.returnToPool(memoryOptimizer.getPooledNode('div'));
            
            const stats = memoryOptimizer.getMemoryStats();
            
            expect(stats).toHaveProperty('cached_objects');
            expect(stats).toHaveProperty('pooled_nodes');
            expect(stats).toHaveProperty('managed_listeners');
            expect(stats).toHaveProperty('js_heap_mb');
            expect(stats.js_heap_mb).toHaveProperty('used');
            expect(stats.js_heap_mb).toHaveProperty('total');
            expect(stats.js_heap_mb).toHaveProperty('limit');
        });
        
        it('should calculate pool efficiency', () => {
            const node = memoryOptimizer.getPooledNode('div');
            node.dataset.poolReused = 'true';
            memoryOptimizer.returnToPool(node);
            
            const stats = memoryOptimizer.getMemoryStats();
            expect(stats.pool_efficiency).toBeGreaterThanOrEqual(0);
        });
    });

    describe('Cleanup functionality', () => {
        it('should perform full cleanup', () => {
            // Add some managed resources
            memoryOptimizer.addManagedListener(document.createElement('div'), 'click', jest.fn());
            memoryOptimizer.returnToPool(memoryOptimizer.getPooledNode('div'));
            memoryOptimizer.observeVisibility(document.createElement('div'), jest.fn());
            
            memoryOptimizer.performFullCleanup();
            
            expect(memoryOptimizer.stats.managed_listeners).toBe(0);
            expect(memoryOptimizer.observedElements.size).toBe(0);
        });
        
        it('should cleanup stale caches', () => {
            // Mock old timestamp
            const oldTimestamp = Date.now() - (11 * 60 * 1000); // 11 minutes ago
            const element = document.createElement('div');
            
            const listenerId = memoryOptimizer.addManagedListener(element, 'click', jest.fn());
            const listener = memoryOptimizer.eventListeners.get(listenerId);
            listener.timestamp = oldTimestamp;
            
            memoryOptimizer.cleanupStaleCaches();
            
            expect(memoryOptimizer.eventListeners.has(listenerId)).toBe(false);
        });
        
        it('should cleanup unused pools', () => {
            // Create oversized pool
            const poolKey = 'div_test';
            const pool = [];
            for (let i = 0; i < 12; i++) {
                pool.push(memoryOptimizer.getPooledNode('div', 'test'));
            }
            pool.forEach(node => memoryOptimizer.returnToPool(node, poolKey));
            
            memoryOptimizer.cleanupUnusedPools();
            
            const currentPool = memoryOptimizer.domNodePool.get(poolKey) || [];
            expect(currentPool.length).toBeLessThanOrEqual(6);
        });
        
        it('should add and execute cleanup callbacks', () => {
            const callback = jest.fn();
            const removeCallback = memoryOptimizer.addCleanupCallback(callback);
            
            memoryOptimizer.performFullCleanup();
            
            expect(callback).toHaveBeenCalled();
            
            // Test callback removal
            removeCallback();
            callback.mockClear();
            
            memoryOptimizer.performFullCleanup();
            expect(callback).not.toHaveBeenCalled();
        });
    });

    describe('Destroy functionality', () => {
        it('should completely destroy optimizer', () => {
            memoryOptimizer.addManagedListener(document.createElement('div'), 'click', jest.fn());
            memoryOptimizer.observeVisibility(document.createElement('div'), jest.fn());
            
            memoryOptimizer.destroy();
            
            expect(memoryOptimizer.weakMapCache).toBeNull();
            expect(memoryOptimizer.eventListeners.size).toBe(0);
            expect(memoryOptimizer.domNodePool.size).toBe(0);
        });
    });
});
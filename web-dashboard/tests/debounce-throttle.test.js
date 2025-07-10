/**
 * Tests for debouncing and throttling optimizations
 */

describe('Performance Optimizations', () => {
    let performanceOptimizer;
    
    beforeEach(() => {
        // Mock browser environment
        global.requestAnimationFrame = jest.fn(cb => setTimeout(cb, 16));
        global.cancelAnimationFrame = jest.fn(clearTimeout);
        global.Date = {
            now: jest.fn(() => 1000)
        };
        
        // Import and create new instance
        const { PerformanceOptimizer } = require('../static/js/utils/debounce-throttle.js');
        performanceOptimizer = new PerformanceOptimizer();
    });

    describe('Debounce functionality', () => {
        it('should debounce function calls', (done) => {
            const mockFn = jest.fn();
            const debouncedFn = performanceOptimizer.debounce(mockFn, 100);
            
            // Call multiple times rapidly
            debouncedFn('call1');
            debouncedFn('call2');
            debouncedFn('call3');
            
            // Should not have been called yet
            expect(mockFn).not.toHaveBeenCalled();
            
            // Should be called once after delay
            setTimeout(() => {
                expect(mockFn).toHaveBeenCalledTimes(1);
                expect(mockFn).toHaveBeenCalledWith('call3');
                done();
            }, 150);
        });

        it('should support immediate execution', () => {
            const mockFn = jest.fn();
            const debouncedFn = performanceOptimizer.debounce(mockFn, 100, { immediate: true });
            
            debouncedFn('immediate');
            
            // Should be called immediately
            expect(mockFn).toHaveBeenCalledTimes(1);
            expect(mockFn).toHaveBeenCalledWith('immediate');
        });

        it('should support maxWait option', (done) => {
            const mockFn = jest.fn();
            const debouncedFn = performanceOptimizer.debounce(mockFn, 100, { maxWait: 200 });
            
            // Call repeatedly to prevent normal execution
            const interval = setInterval(() => {
                debouncedFn('maxwait');
            }, 50);
            
            // Should be forced to execute after maxWait
            setTimeout(() => {
                clearInterval(interval);
                expect(mockFn).toHaveBeenCalledTimes(1);
                done();
            }, 250);
        });
    });

    describe('Throttle functionality', () => {
        it('should throttle function calls', (done) => {
            const mockFn = jest.fn();
            const throttledFn = performanceOptimizer.throttle(mockFn, 100);
            
            // Call multiple times rapidly
            throttledFn('call1');
            throttledFn('call2');
            throttledFn('call3');
            
            // Should be called immediately (leading)
            expect(mockFn).toHaveBeenCalledTimes(1);
            expect(mockFn).toHaveBeenCalledWith('call1');
            
            // Should be called again after throttle period
            setTimeout(() => {
                expect(mockFn).toHaveBeenCalledTimes(2);
                expect(mockFn).toHaveBeenLastCalledWith('call3');
                done();
            }, 150);
        });

        it('should support leading and trailing options', () => {
            const mockFn = jest.fn();
            const throttledFn = performanceOptimizer.throttle(mockFn, 100, { 
                leading: false, 
                trailing: true 
            });
            
            throttledFn('test');
            
            // Should not be called immediately with leading: false
            expect(mockFn).not.toHaveBeenCalled();
        });
    });

    describe('Batch processing', () => {
        it('should batch events and process them together', (done) => {
            const processorFn = jest.fn();
            const batchedFn = performanceOptimizer.batchEvents('test', processorFn, 50);
            
            // Add multiple items to batch
            batchedFn('item1');
            batchedFn('item2');
            batchedFn('item3');
            
            // Should not be processed yet
            expect(processorFn).not.toHaveBeenCalled();
            
            // Should be processed after delay
            setTimeout(() => {
                expect(processorFn).toHaveBeenCalledTimes(1);
                expect(processorFn).toHaveBeenCalledWith([
                    expect.objectContaining({ data: 'item1' }),
                    expect.objectContaining({ data: 'item2' }),
                    expect.objectContaining({ data: 'item3' })
                ]);
                done();
            }, 100);
        });
    });

    describe('Smart updater creation', () => {
        it('should create debounced updater by default', () => {
            const updateFn = jest.fn();
            const smartUpdater = performanceOptimizer.createSmartUpdater(updateFn);
            
            expect(typeof smartUpdater).toBe('function');
            expect(smartUpdater.cancel).toBeDefined();
        });

        it('should create throttled updater when specified', () => {
            const updateFn = jest.fn();
            const smartUpdater = performanceOptimizer.createSmartUpdater(updateFn, {
                strategy: 'throttle',
                throttleTime: 50
            });
            
            smartUpdater('test');
            expect(updateFn).toHaveBeenCalledTimes(1);
        });

        it('should create batched updater when specified', () => {
            const updateFn = jest.fn();
            const smartUpdater = performanceOptimizer.createSmartUpdater(updateFn, {
                strategy: 'batch',
                debounceTime: 50,
                batchKey: 'test'
            });
            
            smartUpdater('test1');
            smartUpdater('test2');
            expect(updateFn).not.toHaveBeenCalled();
        });
    });

    describe('WebSocket optimization', () => {
        it('should optimize session update handlers', () => {
            const handler = jest.fn();
            const optimizedHandler = performanceOptimizer.optimizeWebSocketHandler(handler, 'session_update');
            
            expect(typeof optimizedHandler).toBe('function');
            
            // Test that it handles the message
            optimizedHandler({ type: 'session_update', data: {} });
        });

        it('should apply different strategies for different message types', () => {
            const handler1 = performanceOptimizer.optimizeWebSocketHandler(jest.fn(), 'session_update');
            const handler2 = performanceOptimizer.optimizeWebSocketHandler(jest.fn(), 'log_update');
            const handler3 = performanceOptimizer.optimizeWebSocketHandler(jest.fn(), 'health_update');
            
            expect(typeof handler1).toBe('function');
            expect(typeof handler2).toBe('function');
            expect(typeof handler3).toBe('function');
        });
    });

    describe('Performance statistics', () => {
        it('should track statistics', () => {
            const mockFn = jest.fn();
            const debouncedFn = performanceOptimizer.debounce(mockFn, 50);
            const throttledFn = performanceOptimizer.throttle(mockFn, 50);
            
            debouncedFn('test');
            throttledFn('test');
            
            const stats = performanceOptimizer.getStats();
            
            expect(stats.debounced_calls).toBeGreaterThan(0);
            expect(stats.throttled_calls).toBeGreaterThan(0);
            expect(stats).toHaveProperty('active_throttles');
            expect(stats).toHaveProperty('active_debounces');
            expect(stats).toHaveProperty('batch_queues');
        });

        it('should estimate memory usage', () => {
            const batchedFn = performanceOptimizer.batchEvents('test', jest.fn(), 100);
            batchedFn('item1');
            batchedFn('item2');
            
            const stats = performanceOptimizer.getStats();
            expect(stats.memory_usage.batch_queue_items).toBe(2);
            expect(stats.memory_usage.estimated_kb).toBeGreaterThan(0);
        });
    });

    describe('RAF-based render throttling', () => {
        it('should throttle render calls using RAF', () => {
            const renderFn = jest.fn();
            const throttledRender = performanceOptimizer.throttleRender(renderFn);
            
            // Call multiple times
            throttledRender('render1');
            throttledRender('render2');
            throttledRender('render3');
            
            // Should schedule only one RAF
            expect(global.requestAnimationFrame).toHaveBeenCalledTimes(1);
            
            // Execute the RAF callback
            const rafCallback = global.requestAnimationFrame.mock.calls[0][0];
            rafCallback();
            
            // Should have rendered with the latest args
            expect(renderFn).toHaveBeenCalledTimes(1);
            expect(renderFn).toHaveBeenCalledWith('render3');
            
            expect(performanceOptimizer.getStats().renders_prevented).toBeGreaterThan(0);
        });
    });

    describe('Cleanup functionality', () => {
        it('should clear all optimizations', () => {
            const batchedFn = performanceOptimizer.batchEvents('test', jest.fn(), 100);
            batchedFn('item');
            
            expect(performanceOptimizer.getStats().batch_queues).toBe(1);
            
            performanceOptimizer.clear();
            
            const stats = performanceOptimizer.getStats();
            expect(stats.batch_queues).toBe(0);
            expect(stats.debounced_calls).toBe(0);
            expect(stats.throttled_calls).toBe(0);
        });
    });
});
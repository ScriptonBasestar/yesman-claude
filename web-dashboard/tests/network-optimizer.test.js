/**
 * Tests for Network Optimizer
 */

describe('Network Optimizer', () => {
    let networkOptimizer;
    
    beforeEach(() => {
        // Mock browser environment
        global.TextEncoder = jest.fn().mockImplementation(() => ({
            encode: jest.fn(text => new Uint8Array(text.split('').map(c => c.charCodeAt(0))))
        }));
        
        global.TextDecoder = jest.fn().mockImplementation(() => ({
            decode: jest.fn(bytes => String.fromCharCode.apply(null, bytes))
        }));
        
        // Mock compression streams
        global.CompressionStream = jest.fn().mockImplementation((format) => ({
            writable: {
                getWriter: jest.fn(() => ({
                    write: jest.fn(),
                    close: jest.fn()
                }))
            },
            readable: {
                getReader: jest.fn(() => ({
                    read: jest.fn().mockResolvedValue({
                        value: new Uint8Array([1, 2, 3, 4]),
                        done: true
                    })
                }))
            }
        }));
        
        global.DecompressionStream = jest.fn().mockImplementation((format) => ({
            writable: {
                getWriter: jest.fn(() => ({
                    write: jest.fn(),
                    close: jest.fn()
                }))
            },
            readable: {
                getReader: jest.fn(() => ({
                    read: jest.fn().mockResolvedValue({
                        value: new Uint8Array([1, 2, 3, 4]),
                        done: true
                    })
                }))
            }
        }));
        
        // Import and create new instance
        const { NetworkOptimizer } = require('../static/js/utils/network-optimizer.js');
        networkOptimizer = new NetworkOptimizer();
    });

    describe('Compression support detection', () => {
        it('should detect compression support', () => {
            expect(networkOptimizer.compressionSupported).toBe(true);
        });
    });

    describe('Message compression', () => {
        it('should not compress small messages', async () => {
            const smallData = { test: 'small' };
            const result = await networkOptimizer.compressMessage(smallData);
            
            expect(result.compressed).toBe(false);
            expect(result.originalSize).toBeLessThan(networkOptimizer.compressionThreshold);
        });
        
        it('should compress large messages when supported', async () => {
            const largeData = {
                content: 'x'.repeat(1000),
                items: Array(100).fill({ id: 1, name: 'test', description: 'long description' })
            };
            
            const result = await networkOptimizer.compressMessage(largeData);
            
            expect(result.originalSize).toBeGreaterThan(networkOptimizer.compressionThreshold);
            expect(networkOptimizer.stats.messages_compressed).toBe(1);
        });
        
        it('should minify JSON when compression not available', async () => {
            // Temporarily disable compression
            const originalSupported = networkOptimizer.compressionSupported;
            networkOptimizer.compressionSupported = false;
            
            const data = {
                test: null,
                number: 3.14159265359,
                content: 'x'.repeat(1000)
            };
            
            const result = await networkOptimizer.compressMessage(data);
            
            expect(result.compressed).toBe(false);
            expect(result.data).not.toContain('null');
            expect(result.data).toContain('3.14'); // Rounded number
            
            // Restore compression support
            networkOptimizer.compressionSupported = originalSupported;
        });
    });

    describe('Delta compression', () => {
        it('should create full delta for first update', () => {
            const data = { count: 1, status: 'active' };
            const delta = networkOptimizer.createDelta(data, null, 'test');
            
            expect(delta.type).toBe('full');
            expect(delta.data).toEqual(data);
        });
        
        it('should create noop delta for no changes', () => {
            const data = { count: 1, status: 'active' };
            
            // First update
            networkOptimizer.createDelta(data, null, 'test');
            
            // Second update with same data
            const delta = networkOptimizer.createDelta(data, data, 'test');
            
            expect(delta.type).toBe('noop');
            expect(delta.data).toBeNull();
            expect(delta.size).toBe(0);
        });
        
        it('should create delta for changed data', () => {
            const oldData = { count: 1, status: 'active', items: ['a', 'b'] };
            const newData = { count: 2, status: 'active', items: ['a', 'b', 'c'] };
            
            const delta = networkOptimizer.createDelta(newData, oldData, 'test');
            
            expect(['delta', 'full']).toContain(delta.type);
            if (delta.type === 'delta') {
                expect(delta.data.changes).toBeDefined();
                expect(networkOptimizer.stats.messages_delta).toBe(1);
            }
        });
        
        it('should apply delta correctly', () => {
            const oldData = { count: 1, status: 'active' };
            const newData = { count: 2, status: 'inactive', newField: 'test' };
            
            const delta = networkOptimizer.calculateDelta(oldData, newData);
            const reconstructed = networkOptimizer.applyDelta(delta, oldData);
            
            expect(reconstructed).toEqual(newData);
        });
        
        it('should handle array changes', () => {
            const oldData = { items: [1, 2, 3] };
            const newData = { items: [1, 2, 3, 4] };
            
            const delta = networkOptimizer.calculateDelta(oldData, newData);
            const reconstructed = networkOptimizer.applyDelta(delta, oldData);
            
            expect(reconstructed).toEqual(newData);
        });
        
        it('should handle nested object changes', () => {
            const oldData = {
                user: { id: 1, name: 'John', preferences: { theme: 'dark' } }
            };
            const newData = {
                user: { id: 1, name: 'John', preferences: { theme: 'light', language: 'en' } }
            };
            
            const delta = networkOptimizer.calculateDelta(oldData, newData);
            const reconstructed = networkOptimizer.applyDelta(delta, oldData);
            
            expect(reconstructed).toEqual(newData);
        });
    });

    describe('Message queuing', () => {
        it('should queue messages by priority', () => {
            networkOptimizer.queueMessage('test', { id: 1 }, 'high');
            networkOptimizer.queueMessage('test', { id: 2 }, 'normal');
            networkOptimizer.queueMessage('test', { id: 3 }, 'low');
            
            const queue = networkOptimizer.messageQueue.get('test');
            expect(queue.high).toHaveLength(1);
            expect(queue.normal).toHaveLength(1);
            expect(queue.low).toHaveLength(1);
        });
        
        it('should flush messages in priority order', async () => {
            networkOptimizer.queueMessage('test', { id: 1 }, 'low');
            networkOptimizer.queueMessage('test', { id: 2 }, 'high');
            networkOptimizer.queueMessage('test', { id: 3 }, 'normal');
            
            const flushed = await networkOptimizer.flushMessageQueue('test');
            
            expect(flushed).toHaveLength(3);
            expect(flushed[0].message.id).toBe(2); // High priority first
            expect(flushed[1].message.id).toBe(3); // Normal priority second
            expect(flushed[2].message.id).toBe(1); // Low priority last
        });
        
        it('should respect max message limit', async () => {
            for (let i = 0; i < 15; i++) {
                networkOptimizer.queueMessage('test', { id: i }, 'normal');
            }
            
            const flushed = await networkOptimizer.flushMessageQueue('test', 10);
            
            expect(flushed).toHaveLength(10);
        });
    });

    describe('Request optimization', () => {
        it('should add compression headers', () => {
            const optimized = networkOptimizer.optimizeRequest('/api/data');
            
            expect(optimized.headers['Accept-Encoding']).toContain('gzip');
        });
        
        it('should add cache headers for static resources', () => {
            const optimized = networkOptimizer.optimizeRequest('/static/css/main.css');
            
            expect(optimized.headers['Cache-Control']).toContain('public');
        });
        
        it('should mark large request bodies for compression', () => {
            const largeBody = JSON.stringify({
                data: 'x'.repeat(1000)
            });
            
            const optimized = networkOptimizer.optimizeRequest('/api/upload', {
                method: 'POST',
                body: largeBody
            });
            
            expect(optimized.headers['Content-Encoding']).toBe('gzip');
            expect(optimized._compressBody).toBe(true);
        });
        
        it('should not compress small request bodies', () => {
            const smallBody = JSON.stringify({ test: 'small' });
            
            const optimized = networkOptimizer.optimizeRequest('/api/small', {
                method: 'POST',
                body: smallBody
            });
            
            expect(optimized.headers['Content-Encoding']).toBeUndefined();
            expect(optimized._compressBody).toBeUndefined();
        });
    });

    describe('Binary encoding/decoding', () => {
        it('should encode objects to binary', () => {
            const data = { test: 'value', number: 42 };
            const encoded = networkOptimizer.encodeToBinary(data);
            
            expect(encoded).toBeInstanceOf(Uint8Array);
        });
        
        it('should encode strings to binary', () => {
            const text = 'Hello, World!';
            const encoded = networkOptimizer.encodeToBinary(text);
            
            expect(encoded).toBeInstanceOf(Uint8Array);
        });
        
        it('should decode binary to objects', () => {
            const data = { test: 'value', number: 42 };
            const encoded = networkOptimizer.encodeToBinary(data);
            const decoded = networkOptimizer.decodeFromBinary(encoded);
            
            expect(decoded).toEqual(data);
        });
        
        it('should decode binary to strings', () => {
            const text = 'Hello, World!';
            const encoded = networkOptimizer.encodeToBinary(text);
            const decoded = networkOptimizer.decodeFromBinary(encoded);
            
            expect(decoded).toBe(text);
        });
    });

    describe('Statistics tracking', () => {
        it('should track compression statistics', async () => {
            const largeData = { content: 'x'.repeat(1000) };
            await networkOptimizer.compressMessage(largeData);
            
            const stats = networkOptimizer.getNetworkStats();
            
            expect(stats.messages_compressed).toBe(1);
            expect(stats.original_bytes).toBeGreaterThan(0);
            expect(stats.compressed_bytes).toBeGreaterThan(0);
            expect(stats.compression_ratio).toBeGreaterThanOrEqual(0);
        });
        
        it('should track delta statistics', () => {
            const oldData = { count: 1 };
            const newData = { count: 2 };
            
            networkOptimizer.createDelta(newData, oldData, 'test');
            
            const stats = networkOptimizer.getNetworkStats();
            expect(stats.delta_cache_size).toBe(1);
        });
        
        it('should calculate total network savings', async () => {
            // Create some compression savings
            const largeData = { content: 'x'.repeat(1000) };
            await networkOptimizer.compressMessage(largeData);
            
            // Create some delta savings
            const oldData = { items: Array(100).fill('test') };
            const newData = { items: [...oldData.items, 'new'] };
            networkOptimizer.createDelta(newData, oldData, 'test');
            
            const stats = networkOptimizer.getNetworkStats();
            expect(stats.total_network_savings_kb).toBeGreaterThan(0);
        });
    });

    describe('Cleanup functionality', () => {
        it('should reset statistics and caches', () => {
            networkOptimizer.queueMessage('test', { id: 1 });
            networkOptimizer.createDelta({ test: 1 }, null, 'test');
            
            networkOptimizer.reset();
            
            expect(networkOptimizer.deltaCache.size).toBe(0);
            expect(networkOptimizer.messageQueue.size).toBe(0);
            expect(networkOptimizer.stats.messages_compressed).toBe(0);
        });
        
        it('should destroy optimizer cleanly', () => {
            networkOptimizer.queueMessage('test', { id: 1 });
            
            networkOptimizer.destroy();
            
            expect(networkOptimizer.messageQueue.size).toBe(0);
            expect(networkOptimizer.deltaCache.size).toBe(0);
        });
    });

    describe('Static resource detection', () => {
        it('should identify CSS files as static', () => {
            expect(networkOptimizer.isStaticResource('/static/css/main.css')).toBe(true);
        });
        
        it('should identify JavaScript files as static', () => {
            expect(networkOptimizer.isStaticResource('/static/js/app.js')).toBe(true);
        });
        
        it('should identify images as static', () => {
            expect(networkOptimizer.isStaticResource('/images/logo.png')).toBe(true);
            expect(networkOptimizer.isStaticResource('/assets/icon.svg')).toBe(true);
        });
        
        it('should identify fonts as static', () => {
            expect(networkOptimizer.isStaticResource('/fonts/roboto.woff2')).toBe(true);
        });
        
        it('should not identify API endpoints as static', () => {
            expect(networkOptimizer.isStaticResource('/api/data')).toBe(false);
            expect(networkOptimizer.isStaticResource('/dashboard')).toBe(false);
        });
    });

    describe('Version generation', () => {
        it('should generate unique versions', () => {
            const version1 = networkOptimizer.generateVersion();
            const version2 = networkOptimizer.generateVersion();
            
            expect(version1).not.toBe(version2);
            expect(typeof version1).toBe('string');
            expect(version1).toMatch(/^\d+-[a-z0-9]+$/);
        });
    });
});
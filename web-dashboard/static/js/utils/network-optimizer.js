/**
 * Network Optimizer
 * Advanced network traffic reduction utilities
 */
class NetworkOptimizer {
    constructor() {
        this.compressionThreshold = 500; // bytes
        this.deltaCache = new Map();
        this.messageQueue = new Map();
        this.compressionRatio = 0;
        this.stats = {
            original_bytes: 0,
            compressed_bytes: 0,
            delta_savings: 0,
            messages_compressed: 0,
            messages_delta: 0,
            compression_ratio: 0,
            network_savings_kb: 0
        };
        
        // Initialize compression support
        this.compressionSupported = this.checkCompressionSupport();
        this.textEncoder = new TextEncoder();
        this.textDecoder = new TextDecoder();
    }

    /**
     * Check browser compression support
     */
    checkCompressionSupport() {
        return 'CompressionStream' in window && 'DecompressionStream' in window;
    }

    /**
     * Message compression using modern browser APIs
     */
    async compressMessage(data) {
        const jsonString = JSON.stringify(data);
        const originalBytes = this.textEncoder.encode(jsonString);
        
        // Only compress if message is above threshold
        if (originalBytes.length < this.compressionThreshold) {
            return {
                data: jsonString,
                compressed: false,
                originalSize: originalBytes.length,
                compressedSize: originalBytes.length
            };
        }

        if (!this.compressionSupported) {
            // Fallback: JSON minification
            const minified = this.minifyJSON(data);
            const minifiedBytes = this.textEncoder.encode(minified);
            
            this.stats.original_bytes += originalBytes.length;
            this.stats.compressed_bytes += minifiedBytes.length;
            this.stats.messages_compressed++;
            
            return {
                data: minified,
                compressed: false,
                originalSize: originalBytes.length,
                compressedSize: minifiedBytes.length
            };
        }

        try {
            // Use browser compression API
            const compressedData = await this.compressWithGzip(originalBytes);
            
            this.stats.original_bytes += originalBytes.length;
            this.stats.compressed_bytes += compressedData.length;
            this.stats.messages_compressed++;
            this.updateCompressionRatio();
            
            return {
                data: compressedData,
                compressed: true,
                originalSize: originalBytes.length,
                compressedSize: compressedData.length
            };
        } catch (error) {
            console.warn('Compression failed, falling back to uncompressed:', error);
            return {
                data: jsonString,
                compressed: false,
                originalSize: originalBytes.length,
                compressedSize: originalBytes.length
            };
        }
    }

    /**
     * Message decompression
     */
    async decompressMessage(compressedData, isCompressed) {
        if (!isCompressed) {
            return typeof compressedData === 'string' ? 
                JSON.parse(compressedData) : 
                compressedData;
        }

        if (!this.compressionSupported) {
            throw new Error('Compression not supported for decompression');
        }

        try {
            const decompressedBytes = await this.decompressWithGzip(compressedData);
            const jsonString = this.textDecoder.decode(decompressedBytes);
            return JSON.parse(jsonString);
        } catch (error) {
            console.error('Decompression failed:', error);
            throw error;
        }
    }

    /**
     * Gzip compression using streams
     */
    async compressWithGzip(data) {
        const stream = new CompressionStream('gzip');
        const writer = stream.writable.getWriter();
        const reader = stream.readable.getReader();
        
        // Write data
        writer.write(data);
        writer.close();
        
        // Read compressed result
        const chunks = [];
        let done = false;
        
        while (!done) {
            const { value, done: readerDone } = await reader.read();
            done = readerDone;
            if (value) {
                chunks.push(value);
            }
        }
        
        // Combine chunks
        const totalLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
        const result = new Uint8Array(totalLength);
        let offset = 0;
        
        for (const chunk of chunks) {
            result.set(chunk, offset);
            offset += chunk.length;
        }
        
        return result;
    }

    /**
     * Gzip decompression using streams
     */
    async decompressWithGzip(compressedData) {
        const stream = new DecompressionStream('gzip');
        const writer = stream.writable.getWriter();
        const reader = stream.readable.getReader();
        
        // Write compressed data
        writer.write(compressedData);
        writer.close();
        
        // Read decompressed result
        const chunks = [];
        let done = false;
        
        while (!done) {
            const { value, done: readerDone } = await reader.read();
            done = readerDone;
            if (value) {
                chunks.push(value);
            }
        }
        
        // Combine chunks
        const totalLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
        const result = new Uint8Array(totalLength);
        let offset = 0;
        
        for (const chunk of chunks) {
            result.set(chunk, offset);
            offset += chunk.length;
        }
        
        return result;
    }

    /**
     * JSON minification fallback
     */
    minifyJSON(data) {
        // Remove unnecessary whitespace and optimize structure
        return JSON.stringify(data, (key, value) => {
            // Remove null values
            if (value === null) return undefined;
            // Round floating point numbers
            if (typeof value === 'number' && !Number.isInteger(value)) {
                return Math.round(value * 100) / 100;
            }
            return value;
        });
    }

    /**
     * Delta compression for incremental updates
     */
    createDelta(currentData, previousData, key) {
        if (!previousData) {
            // First time - store full data
            this.deltaCache.set(key, currentData);
            return {
                type: 'full',
                data: currentData,
                size: JSON.stringify(currentData).length
            };
        }

        const delta = this.calculateDelta(previousData, currentData);
        
        if (delta.changes.length === 0) {
            // No changes
            return {
                type: 'noop',
                data: null,
                size: 0
            };
        }

        const deltaSize = JSON.stringify(delta).length;
        const fullSize = JSON.stringify(currentData).length;
        
        // Use delta if it's significantly smaller
        if (deltaSize < fullSize * 0.7) {
            this.deltaCache.set(key, currentData);
            this.stats.delta_savings += (fullSize - deltaSize);
            this.stats.messages_delta++;
            
            return {
                type: 'delta',
                data: delta,
                size: deltaSize
            };
        } else {
            // Delta not efficient, send full data
            this.deltaCache.set(key, currentData);
            return {
                type: 'full',
                data: currentData,
                size: fullSize
            };
        }
    }

    /**
     * Apply delta to reconstruct full data
     */
    applyDelta(delta, baseData) {
        const result = JSON.parse(JSON.stringify(baseData)); // Deep clone
        
        for (const change of delta.changes) {
            this.applyChange(result, change);
        }
        
        return result;
    }

    /**
     * Calculate delta between two objects
     */
    calculateDelta(oldData, newData) {
        const changes = [];
        this.findChanges(oldData, newData, '', changes);
        
        return {
            version: this.generateVersion(),
            changes: changes
        };
    }

    /**
     * Find changes between objects recursively
     */
    findChanges(oldObj, newObj, path, changes) {
        // Handle arrays
        if (Array.isArray(oldObj) && Array.isArray(newObj)) {
            // Simple array comparison - optimize later for large arrays
            if (JSON.stringify(oldObj) !== JSON.stringify(newObj)) {
                changes.push({
                    op: 'replace',
                    path: path,
                    value: newObj
                });
            }
            return;
        }

        // Handle objects
        if (typeof oldObj === 'object' && typeof newObj === 'object' && oldObj && newObj) {
            // Check for removed properties
            for (const key in oldObj) {
                if (!(key in newObj)) {
                    changes.push({
                        op: 'remove',
                        path: path ? `${path}.${key}` : key
                    });
                }
            }

            // Check for added or modified properties
            for (const key in newObj) {
                const newPath = path ? `${path}.${key}` : key;
                
                if (!(key in oldObj)) {
                    // Added property
                    changes.push({
                        op: 'add',
                        path: newPath,
                        value: newObj[key]
                    });
                } else if (oldObj[key] !== newObj[key]) {
                    // Modified property
                    if (typeof oldObj[key] === 'object' && typeof newObj[key] === 'object') {
                        // Recurse for nested objects
                        this.findChanges(oldObj[key], newObj[key], newPath, changes);
                    } else {
                        // Replace primitive value
                        changes.push({
                            op: 'replace',
                            path: newPath,
                            value: newObj[key]
                        });
                    }
                }
            }
        } else if (oldObj !== newObj) {
            // Different primitive values
            changes.push({
                op: 'replace',
                path: path,
                value: newObj
            });
        }
    }

    /**
     * Apply a single change to an object
     */
    applyChange(obj, change) {
        const pathParts = change.path.split('.');
        let current = obj;
        
        // Navigate to parent
        for (let i = 0; i < pathParts.length - 1; i++) {
            if (!(pathParts[i] in current)) {
                current[pathParts[i]] = {};
            }
            current = current[pathParts[i]];
        }
        
        const finalKey = pathParts[pathParts.length - 1];
        
        switch (change.op) {
            case 'add':
            case 'replace':
                current[finalKey] = change.value;
                break;
            case 'remove':
                delete current[finalKey];
                break;
        }
    }

    /**
     * Message queuing for batch optimization
     */
    queueMessage(channel, message, priority = 'normal') {
        if (!this.messageQueue.has(channel)) {
            this.messageQueue.set(channel, {
                high: [],
                normal: [],
                low: []
            });
        }
        
        this.messageQueue.get(channel)[priority].push({
            message,
            timestamp: Date.now()
        });
    }

    /**
     * Flush message queue with optimization
     */
    async flushMessageQueue(channel, maxMessages = 10) {
        const queue = this.messageQueue.get(channel);
        if (!queue) return [];

        const messages = [];
        
        // Prioritize high priority messages
        const priorities = ['high', 'normal', 'low'];
        let totalMessages = 0;
        
        for (const priority of priorities) {
            while (queue[priority].length > 0 && totalMessages < maxMessages) {
                messages.push(queue[priority].shift());
                totalMessages++;
            }
        }
        
        if (messages.length === 0) return [];

        // Optimize batch
        return await this.optimizeBatch(messages);
    }

    /**
     * Optimize a batch of messages
     */
    async optimizeBatch(messages) {
        if (messages.length === 1) {
            // Single message - apply standard optimizations
            const msg = messages[0];
            const compressed = await this.compressMessage(msg.message);
            return [{
                ...msg,
                optimized: compressed
            }];
        }

        // Multiple messages - look for commonalities and delta opportunities
        const optimized = [];
        
        for (let i = 0; i < messages.length; i++) {
            const msg = messages[i];
            const compressed = await this.compressMessage(msg.message);
            
            optimized.push({
                ...msg,
                optimized: compressed
            });
        }
        
        return optimized;
    }

    /**
     * Request/Response optimization
     */
    optimizeRequest(url, options = {}) {
        const optimizedOptions = { ...options };
        
        // Add compression headers
        if (!optimizedOptions.headers) {
            optimizedOptions.headers = {};
        }
        
        if (this.compressionSupported) {
            optimizedOptions.headers['Accept-Encoding'] = 'gzip, deflate, br';
        }
        
        // Add cache control for static resources
        if (this.isStaticResource(url)) {
            optimizedOptions.headers['Cache-Control'] = 'public, max-age=3600';
        }
        
        // Enable compression for request body
        if (optimizedOptions.body && typeof optimizedOptions.body === 'string') {
            const bodySize = this.textEncoder.encode(optimizedOptions.body).length;
            if (bodySize > this.compressionThreshold) {
                // Mark for compression
                optimizedOptions.headers['Content-Encoding'] = 'gzip';
                optimizedOptions._compressBody = true;
            }
        }
        
        return optimizedOptions;
    }

    /**
     * Check if URL is for static resource
     */
    isStaticResource(url) {
        const staticExtensions = ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2'];
        return staticExtensions.some(ext => url.includes(ext));
    }

    /**
     * Binary protocol helpers
     */
    encodeToBinary(data) {
        // Simple binary encoding for common data types
        if (typeof data === 'object') {
            const json = JSON.stringify(data);
            return this.textEncoder.encode(json);
        }
        
        if (typeof data === 'string') {
            return this.textEncoder.encode(data);
        }
        
        return data;
    }

    decodeFromBinary(binaryData) {
        const text = this.textDecoder.decode(binaryData);
        try {
            return JSON.parse(text);
        } catch {
            return text;
        }
    }

    /**
     * Generate version for delta tracking
     */
    generateVersion() {
        return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Update compression ratio
     */
    updateCompressionRatio() {
        if (this.stats.original_bytes > 0) {
            this.stats.compression_ratio = 
                Math.round((1 - this.stats.compressed_bytes / this.stats.original_bytes) * 100);
            this.stats.network_savings_kb = 
                Math.round((this.stats.original_bytes - this.stats.compressed_bytes) / 1024 * 100) / 100;
        }
    }

    /**
     * Get network optimization statistics
     */
    getNetworkStats() {
        this.updateCompressionRatio();
        
        return {
            ...this.stats,
            compression_supported: this.compressionSupported,
            delta_cache_size: this.deltaCache.size,
            queue_size: Array.from(this.messageQueue.values())
                .reduce((total, queue) => total + queue.high.length + queue.normal.length + queue.low.length, 0),
            average_compression_ratio: this.stats.compression_ratio,
            total_network_savings_kb: this.stats.network_savings_kb + (this.stats.delta_savings / 1024)
        };
    }

    /**
     * Clear caches and reset stats
     */
    reset() {
        this.deltaCache.clear();
        this.messageQueue.clear();
        this.stats = {
            original_bytes: 0,
            compressed_bytes: 0,
            delta_savings: 0,
            messages_compressed: 0,
            messages_delta: 0,
            compression_ratio: 0,
            network_savings_kb: 0
        };
    }

    /**
     * Cleanup resources
     */
    destroy() {
        this.reset();
    }
}

// Global network optimizer instance
window.networkOptimizer = new NetworkOptimizer();

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { NetworkOptimizer };
}
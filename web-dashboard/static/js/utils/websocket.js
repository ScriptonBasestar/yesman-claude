/**
 * WebSocket Manager for real-time updates
 * Handles WebSocket connections with auto-reconnect and event system
 */

class WebSocketManager {
    constructor() {
        this.connections = new Map(); // channel -> WebSocket
        this.eventHandlers = new Map(); // event -> Set of handlers
        this.reconnectAttempts = new Map(); // channel -> attempt count
        this.reconnectTimeouts = new Map(); // channel -> timeout ID
        
        // Configuration
        this.config = {
            maxReconnectAttempts: 10,
            reconnectDelay: 1000, // Start with 1 second
            maxReconnectDelay: 30000, // Max 30 seconds
            heartbeatInterval: 30000, // 30 seconds
            connectionTimeout: 5000, // 5 seconds to establish connection
            debug: false
        };
        
        // Connection states
        this.states = {
            CONNECTING: 0,
            OPEN: 1,
            CLOSING: 2,
            CLOSED: 3
        };
        
        // Heartbeat intervals
        this.heartbeatIntervals = new Map();
        
        // Initialize event handlers map
        this.initializeEventHandlers();
        
        // Bind methods
        this.connect = this.connect.bind(this);
        this.disconnect = this.disconnect.bind(this);
        this.send = this.send.bind(this);
    }
    
    initializeEventHandlers() {
        // Pre-initialize common event types
        const eventTypes = [
            'connected', 'disconnected', 'error', 'reconnecting',
            'session_update', 'health_update', 'activity_update',
            'log_update', 'initial_data', 'ping', 'pong'
        ];
        
        eventTypes.forEach(event => {
            this.eventHandlers.set(event, new Set());
        });
    }
    
    /**
     * Connect to a WebSocket channel
     * @param {string} channel - Channel name (dashboard, sessions, health, activity)
     * @returns {Promise<void>}
     */
    async connect(channel = 'dashboard') {
        if (this.connections.has(channel)) {
            this.log(`Already connected to channel: ${channel}`);
            return;
        }
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const url = `${protocol}//${host}/ws/${channel}`;
        
        this.log(`Connecting to ${url}`);
        
        try {
            const ws = await this.createConnection(url, channel);
            this.connections.set(channel, ws);
            this.reconnectAttempts.set(channel, 0);
            this.setupEventHandlers(ws, channel);
            this.startHeartbeat(channel);
            
        } catch (error) {
            this.log(`Failed to connect to ${channel}:`, error);
            this.emit('error', { channel, error });
            this.scheduleReconnect(channel);
        }
    }
    
    /**
     * Create WebSocket connection with timeout
     */
    createConnection(url, channel) {
        return new Promise((resolve, reject) => {
            const ws = new WebSocket(url);
            let connectionTimeout;
            
            // Set connection timeout
            connectionTimeout = setTimeout(() => {
                ws.close();
                reject(new Error('Connection timeout'));
            }, this.config.connectionTimeout);
            
            ws.onopen = () => {
                clearTimeout(connectionTimeout);
                this.log(`Connected to ${channel}`);
                resolve(ws);
            };
            
            ws.onerror = (error) => {
                clearTimeout(connectionTimeout);
                reject(error);
            };
        });
    }
    
    /**
     * Setup event handlers for WebSocket
     */
    setupEventHandlers(ws, channel) {
        ws.onopen = () => {
            this.log(`WebSocket opened for ${channel}`);
            this.emit('connected', { channel });
        };
        
        ws.onclose = (event) => {
            this.log(`WebSocket closed for ${channel}`, event);
            this.handleDisconnection(channel, event);
        };
        
        ws.onerror = (error) => {
            this.log(`WebSocket error for ${channel}:`, error);
            this.emit('error', { channel, error });
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(channel, data);
            } catch (error) {
                this.log('Failed to parse message:', error);
            }
        };
    }
    
    /**
     * Handle incoming WebSocket messages
     */
    handleMessage(channel, data) {
        const messageType = data.type;
        
        // Handle ping-pong
        if (messageType === 'ping') {
            this.send(channel, { type: 'pong', timestamp: new Date().toISOString() });
            return;
        }
        
        // Handle message batches
        if (messageType === 'message_batch') {
            this.handleMessageBatch(channel, data);
            return;
        }
        
        // Emit message to handlers (with optimization)
        this.emitOptimized(messageType, data);
        
        // Also emit a generic message event
        this.emit('message', { channel, data });
    }
    
    /**
     * Handle batched messages from server
     */
    handleMessageBatch(channel, batchData) {
        const messages = batchData.messages || [];
        const batchInfo = {
            channel,
            count: batchData.count,
            timestamp: batchData.timestamp
        };
        
        // Process each message in the batch
        messages.forEach(message => {
            this.emitOptimized(message.type, message);
        });
        
        // Emit batch completion event
        this.emit('batch_processed', batchInfo);
    }
    
    /**
     * Emit events with performance optimization
     */
    emitOptimized(event, data) {
        // Use optimized handlers if available
        if (window.performanceOptimizer) {
            const optimizedEmit = this.getOptimizedEmitter(event);
            optimizedEmit(data);
        } else {
            this.emit(event, data);
        }
    }
    
    /**
     * Get or create optimized emitter for event type
     */
    getOptimizedEmitter(event) {
        if (!this._optimizedEmitters) {
            this._optimizedEmitters = new Map();
        }
        
        if (!this._optimizedEmitters.has(event)) {
            const baseEmitter = (data) => this.emit(event, data);
            const optimizedEmitter = window.performanceOptimizer.optimizeWebSocketHandler(
                baseEmitter, 
                event
            );
            this._optimizedEmitters.set(event, optimizedEmitter);
        }
        
        return this._optimizedEmitters.get(event);
    }
    
    /**
     * Handle disconnection and schedule reconnect
     */
    handleDisconnection(channel, event) {
        // Clean up
        this.connections.delete(channel);
        this.stopHeartbeat(channel);
        
        // Emit disconnected event
        this.emit('disconnected', { channel, code: event.code, reason: event.reason });
        
        // Check if we should reconnect
        if (event.code !== 1000) { // 1000 = normal closure
            this.scheduleReconnect(channel);
        }
    }
    
    /**
     * Schedule reconnection with exponential backoff
     */
    scheduleReconnect(channel) {
        const attempts = this.reconnectAttempts.get(channel) || 0;
        
        if (attempts >= this.config.maxReconnectAttempts) {
            this.log(`Max reconnection attempts reached for ${channel}`);
            this.emit('error', { 
                channel, 
                error: new Error('Max reconnection attempts reached') 
            });
            return;
        }
        
        // Calculate delay with exponential backoff
        const delay = Math.min(
            this.config.reconnectDelay * Math.pow(2, attempts),
            this.config.maxReconnectDelay
        );
        
        this.log(`Scheduling reconnect for ${channel} in ${delay}ms (attempt ${attempts + 1})`);
        this.emit('reconnecting', { channel, attempt: attempts + 1, delay });
        
        const timeoutId = setTimeout(() => {
            this.reconnectAttempts.set(channel, attempts + 1);
            this.connect(channel);
        }, delay);
        
        this.reconnectTimeouts.set(channel, timeoutId);
    }
    
    /**
     * Disconnect from a channel
     */
    disconnect(channel) {
        // Cancel any pending reconnects
        const timeoutId = this.reconnectTimeouts.get(channel);
        if (timeoutId) {
            clearTimeout(timeoutId);
            this.reconnectTimeouts.delete(channel);
        }
        
        // Stop heartbeat
        this.stopHeartbeat(channel);
        
        // Close connection
        const ws = this.connections.get(channel);
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.close(1000, 'Client disconnect');
            this.connections.delete(channel);
        }
        
        // Reset reconnect attempts
        this.reconnectAttempts.delete(channel);
    }
    
    /**
     * Send data to a channel
     */
    send(channel, data) {
        const ws = this.connections.get(channel);
        
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            this.log(`Cannot send to ${channel}: not connected`);
            return false;
        }
        
        try {
            ws.send(JSON.stringify(data));
            return true;
        } catch (error) {
            this.log(`Failed to send to ${channel}:`, error);
            return false;
        }
    }
    
    /**
     * Subscribe to multiple channels
     */
    subscribe(channels) {
        if (!Array.isArray(channels)) {
            channels = [channels];
        }
        
        const ws = this.connections.get('dashboard');
        if (ws && ws.readyState === WebSocket.OPEN) {
            this.send('dashboard', {
                type: 'subscribe',
                channels: channels
            });
        }
    }
    
    /**
     * Unsubscribe from channels
     */
    unsubscribe(channels) {
        if (!Array.isArray(channels)) {
            channels = [channels];
        }
        
        const ws = this.connections.get('dashboard');
        if (ws && ws.readyState === WebSocket.OPEN) {
            this.send('dashboard', {
                type: 'unsubscribe',
                channels: channels
            });
        }
    }
    
    /**
     * Start heartbeat for a channel
     */
    startHeartbeat(channel) {
        const intervalId = setInterval(() => {
            const ws = this.connections.get(channel);
            if (ws && ws.readyState === WebSocket.OPEN) {
                // Server sends ping, we just need to respond
                // This interval is for monitoring connection health
                if (ws.readyState !== WebSocket.OPEN) {
                    this.handleDisconnection(channel, { code: 4000, reason: 'Connection lost' });
                }
            }
        }, this.config.heartbeatInterval);
        
        this.heartbeatIntervals.set(channel, intervalId);
    }
    
    /**
     * Stop heartbeat for a channel
     */
    stopHeartbeat(channel) {
        const intervalId = this.heartbeatIntervals.get(channel);
        if (intervalId) {
            clearInterval(intervalId);
            this.heartbeatIntervals.delete(channel);
        }
    }
    
    /**
     * Register event handler
     */
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, new Set());
        }
        
        this.eventHandlers.get(event).add(handler);
        
        // Return unsubscribe function
        return () => {
            this.off(event, handler);
        };
    }
    
    /**
     * Unregister event handler
     */
    off(event, handler) {
        const handlers = this.eventHandlers.get(event);
        if (handlers) {
            handlers.delete(handler);
        }
    }
    
    /**
     * Emit event to handlers
     */
    emit(event, data) {
        const handlers = this.eventHandlers.get(event);
        if (handlers) {
            handlers.forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${event}:`, error);
                }
            });
        }
    }
    
    /**
     * Get connection state for a channel
     */
    getState(channel) {
        const ws = this.connections.get(channel);
        if (!ws) {
            return this.states.CLOSED;
        }
        return ws.readyState;
    }
    
    /**
     * Check if connected to a channel
     */
    isConnected(channel) {
        return this.getState(channel) === this.states.OPEN;
    }
    
    /**
     * Get all active channels
     */
    getActiveChannels() {
        return Array.from(this.connections.keys()).filter(channel => 
            this.isConnected(channel)
        );
    }
    
    /**
     * Disconnect from all channels
     */
    disconnectAll() {
        this.connections.forEach((ws, channel) => {
            this.disconnect(channel);
        });
    }
    
    /**
     * Enable/disable debug logging
     */
    setDebug(enabled) {
        this.config.debug = enabled;
    }
    
    /**
     * Internal logging
     */
    log(...args) {
        if (this.config.debug) {
            console.log('[WebSocketManager]', ...args);
        }
    }
}

// Export as singleton
const wsManager = new WebSocketManager();

// Also export class for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { WebSocketManager, wsManager };
}
"""WebSocket router for real-time updates"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set, List
import asyncio
import json
import logging
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """Manages WebSocket connections and broadcasting"""
    
    def __init__(self):
        # All active connections
        self.active_connections: List[WebSocket] = []
        
        # Channel-based connections
        self.channel_connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict] = {}
        
        # Ping interval in seconds
        self.ping_interval = 30
        
        # Start background tasks
        self.start_background_tasks()
    
    def start_background_tasks(self):
        """Start background tasks for connection management"""
        asyncio.create_task(self.ping_connections())
    
    async def connect(self, websocket: WebSocket, channel: str = "dashboard"):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.channel_connections[channel].add(websocket)
        
        # Store metadata
        self.connection_metadata[websocket] = {
            "channel": channel,
            "connected_at": datetime.now(),
            "last_ping": datetime.now()
        }
        
        logger.info(f"WebSocket connected to channel: {channel}")
        
        # Send initial data
        await self.send_initial_data(websocket, channel)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from all channels
        for channel, connections in self.channel_connections.items():
            if websocket in connections:
                connections.remove(websocket)
        
        # Clean up metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
        
        logger.info("WebSocket disconnected")
    
    async def send_initial_data(self, websocket: WebSocket, channel: str):
        """Send initial data when a client connects"""
        try:
            # Import here to avoid circular imports
            from api.routers.dashboard import get_sessions, get_project_health, get_activity_data, get_dashboard_stats
            
            initial_data = {}
            
            if channel in ["dashboard", "sessions"]:
                sessions = await get_sessions()
                initial_data["sessions"] = sessions
            
            if channel in ["dashboard", "health"]:
                health = await get_project_health()
                initial_data["health"] = health
            
            if channel in ["dashboard", "activity"]:
                activity = await get_activity_data()
                initial_data["activity"] = activity
            
            if channel == "dashboard":
                stats = await get_dashboard_stats()
                initial_data["stats"] = stats
            
            message = {
                "type": "initial_data",
                "timestamp": datetime.now().isoformat(),
                "channel": channel,
                "data": initial_data
            }
            
            await websocket.send_json(message)
            
        except Exception as e:
            logger.error(f"Error sending initial data: {str(e)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {str(e)}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {str(e)}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_to_channel(self, channel: str, message: dict):
        """Broadcast message to specific channel"""
        disconnected = []
        connections = self.channel_connections.get(channel, set())
        
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to channel {channel}: {str(e)}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_session_update(self, session_data: dict):
        """Broadcast session update to relevant channels"""
        message = {
            "type": "session_update",
            "timestamp": datetime.now().isoformat(),
            "data": session_data
        }
        
        await self.broadcast_to_channel("sessions", message)
        await self.broadcast_to_channel("dashboard", message)
    
    async def broadcast_health_update(self, health_data: dict):
        """Broadcast health update to relevant channels"""
        message = {
            "type": "health_update",
            "timestamp": datetime.now().isoformat(),
            "data": health_data
        }
        
        await self.broadcast_to_channel("health", message)
        await self.broadcast_to_channel("dashboard", message)
    
    async def broadcast_activity_update(self, activity_data: dict):
        """Broadcast activity update to relevant channels"""
        message = {
            "type": "activity_update",
            "timestamp": datetime.now().isoformat(),
            "data": activity_data
        }
        
        await self.broadcast_to_channel("activity", message)
        await self.broadcast_to_channel("dashboard", message)
    
    async def ping_connections(self):
        """Send periodic ping messages to keep connections alive"""
        while True:
            await asyncio.sleep(self.ping_interval)
            
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_json({
                        "type": "ping",
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Update last ping time
                    if connection in self.connection_metadata:
                        self.connection_metadata[connection]["last_ping"] = datetime.now()
                        
                except Exception as e:
                    logger.error(f"Error pinging connection: {str(e)}")
                    disconnected.append(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                self.disconnect(conn)
    
    def get_connection_stats(self):
        """Get statistics about active connections"""
        stats = {
            "total_connections": len(self.active_connections),
            "channels": {}
        }
        
        for channel, connections in self.channel_connections.items():
            stats["channels"][channel] = len(connections)
        
        return stats


# Create global connection manager instance
manager = ConnectionManager()


@router.websocket("/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """Main dashboard WebSocket endpoint"""
    await manager.connect(websocket, "dashboard")
    
    try:
        while True:
            # Receive and process messages
            data = await websocket.receive_json()
            
            # Handle different message types
            if data.get("type") == "pong":
                # Client responded to ping
                logger.debug("Received pong from dashboard client")
            
            elif data.get("type") == "subscribe":
                # Client wants to subscribe to specific updates
                channels = data.get("channels", [])
                for channel in channels:
                    manager.channel_connections[channel].add(websocket)
                    logger.info(f"Dashboard client subscribed to channel: {channel}")
            
            elif data.get("type") == "unsubscribe":
                # Client wants to unsubscribe from specific updates
                channels = data.get("channels", [])
                for channel in channels:
                    if websocket in manager.channel_connections[channel]:
                        manager.channel_connections[channel].remove(websocket)
                        logger.info(f"Dashboard client unsubscribed from channel: {channel}")
            
            else:
                # Echo back unknown messages for debugging
                await manager.send_personal_message({
                    "type": "echo",
                    "original": data,
                    "timestamp": datetime.now().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Dashboard WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)


@router.websocket("/sessions")
async def websocket_sessions(websocket: WebSocket):
    """Sessions-specific WebSocket endpoint"""
    await manager.connect(websocket, "sessions")
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "pong":
                logger.debug("Received pong from sessions client")
            
            elif data.get("type") == "refresh":
                # Client requests fresh session data
                await manager.send_initial_data(websocket, "sessions")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Sessions WebSocket disconnected")
    except Exception as e:
        logger.error(f"Sessions WebSocket error: {str(e)}")
        manager.disconnect(websocket)


@router.websocket("/health")
async def websocket_health(websocket: WebSocket):
    """Health metrics WebSocket endpoint"""
    await manager.connect(websocket, "health")
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "pong":
                logger.debug("Received pong from health client")
            
            elif data.get("type") == "refresh":
                # Client requests fresh health data
                await manager.send_initial_data(websocket, "health")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Health WebSocket disconnected")
    except Exception as e:
        logger.error(f"Health WebSocket error: {str(e)}")
        manager.disconnect(websocket)


@router.websocket("/activity")
async def websocket_activity(websocket: WebSocket):
    """Activity data WebSocket endpoint"""
    await manager.connect(websocket, "activity")
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "pong":
                logger.debug("Received pong from activity client")
            
            elif data.get("type") == "refresh":
                # Client requests fresh activity data
                await manager.send_initial_data(websocket, "activity")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Activity WebSocket disconnected")
    except Exception as e:
        logger.error(f"Activity WebSocket error: {str(e)}")
        manager.disconnect(websocket)


# Export manager for use in other modules
__all__ = ["router", "manager"]
# backend/app/websocket_manager.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Set, Dict, Optional
import asyncio
import json
from datetime import datetime
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class WebSocketManager:
    """Manage WebSocket connections and broadcasts."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_count = 0
        self.message_count = 0
    
    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept and register a new WebSocket connection.
        """
        try:
            await websocket.accept()
            self.active_connections.add(websocket)
            self.connection_count += 1
            logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        except Exception as e:
            logger.error(f"Error accepting WebSocket connection: {str(e)}")
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Unregister and close a WebSocket connection.
        """
        try:
            self.active_connections.discard(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket: {str(e)}")
    
    async def broadcast(self, message: Dict) -> None:
        """
        Broadcast a message to all connected clients.
        """
        if not self.active_connections:
            return
        
        try:
            message_json = json.dumps(message)
            self.message_count += 1
            
            # Use list() to avoid "Set changed size during iteration" errors
            disconnected_connections = set()
            
            for connection in list(self.active_connections):
                try:
                    await connection.send_text(message_json)
                except Exception as e:
                    logger.warning(f"Error sending message to client: {str(e)}")
                    disconnected_connections.add(connection)
            
            # Remove disconnected clients
            for connection in disconnected_connections:
                await self.disconnect(connection)
        
        except Exception as e:
            logger.error(f"Error broadcasting message: {str(e)}")
    
    async def send_personal_message(self, message: Dict, websocket: WebSocket) -> None:
        """
        Send a message to a specific client.
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {str(e)}")
            await self.disconnect(websocket)
    
    def get_stats(self) -> Dict:
        """Get WebSocket statistics."""
        return {
            'active_connections': len(self.active_connections),
            'total_connections': self.connection_count,
            'total_messages_sent': self.message_count
        }

# Global manager instance
manager = WebSocketManager()
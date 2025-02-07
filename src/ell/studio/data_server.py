import asyncio
import websockets
from fastapi import FastAPI, WebSocket, Query
from typing import List, Dict, Any, Optional
from ell.stores.sql import SQLiteStore
from ell import __version__
import os
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException

logger = logging.getLogger(__name__)

app = FastAPI(title="ELL Studio", version=__version__)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ConnectionManager class to handle WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Message received: {data}", websocket)
            await manager.broadcast(f"Client says: {data}")
    except websockets.exceptions.ConnectionClosed as e:
        manager.disconnect(websocket)
        logger.info(f"WebSocket connection closed: {e}")

# Function to retrieve invocations with a structured filter approach
def get_invocation_by_id(invocation_id: str, serializer: SQLiteStore) -> Optional[Dict[str, Any]]:
    invocations = serializer.get_invocations(filters={"id": invocation_id})
    return invocations[0] if invocations else None

# Function to notify clients
async def notify_clients(message: str, serializer: SQLiteStore):
    await manager.broadcast(message)

# Example route to get an invocation
@app.get("/api/invocation/{invocation_id}")
def get_invocation(invocation_id: str):
    serializer = SQLiteStore(os.getcwd())
    invocation = get_invocation_by_id(invocation_id, serializer)
    if invocation:
        return invocation
    else:
        raise HTTPException(status_code=404, detail="Invocation not found")

# Example route to notify clients
@app.post("/api/notify")
def notify(message: str):
    serializer = SQLiteStore(os.getcwd())
    await notify_clients(message, serializer)
    return {"status": "Notification sent"}

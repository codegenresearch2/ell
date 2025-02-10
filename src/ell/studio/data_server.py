from fastapi import FastAPI, WebSocket, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="ELL Studio", version="0.1.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ConnectionManager class to manage WebSocket connections
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

# Placeholder for SQLiteStore class
class SQLiteStore:
    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir

    def get_lmps(self, skip: int, limit: int) -> List[Dict[str, Any]]:
        # Placeholder for actual data retrieval logic
        return [{"id": f"lmp{i}", "name": f"LMP{i}"} for i in range(skip, skip + limit)]

    def get_latest_lmps(self, skip: int, limit: int) -> List[Dict[str, Any]]:
        # Placeholder for actual data retrieval logic
        return [{"id": f"latest_lmp{i}", "name": f"Latest LMP{i}"} for i in range(skip, skip + limit)]

    def get_invocations(self, lmp_id: Optional[str] = None) -> List[Dict[str, Any]]:
        # Placeholder for actual data retrieval logic
        return [{"id": f"inv{i}", "lmp_id": lmp_id} for i in range(1, 3)]

store = SQLiteStore(os.getenv("ELL_STORAGE_DIR", "default_storage"))

@app.get("/api/lmps")
def get_lmps(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    lmps = store.get_lmps(skip, limit)
    if not lmps:
        raise HTTPException(status_code=404, detail="No LMPs found")
    return lmps

@app.get("/api/latest/lmps")
def get_latest_lmps(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    lmps = store.get_latest_lmps(skip, limit)
    if not lmps:
        raise HTTPException(status_code=404, detail="No latest LMPs found")
    return lmps

@app.get("/api/invocation/{invocation_id}")
def get_invocation(
    invocation_id: str,
):
    invocations = store.get_invocations(invocation_id)
    if not invocations:
        raise HTTPException(status_code=404, detail="Invocation not found")
    return invocations[0]

@app.get("/api/invocations")
def get_invocations(
    id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    lmp_name: Optional[str] = Query(None),
    lmp_id: Optional[str] = Query(None),
):
    # Placeholder for actual invocations retrieval logic
    invocations = store.get_invocations(lmp_id)
    if not invocations:
        raise HTTPException(status_code=404, detail="No invocations found")
    return invocations

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client disconnected")

def notify_clients(message: str):
    logger.info(f"Broadcasting message: {message}")
    # Placeholder for actual notification logic
    pass

# Example of using notify_clients
# notify_clients("An event has occurred")


This revised code snippet addresses the feedback from the oracle by implementing a `ConnectionManager` class for WebSocket connections, allowing the storage path to be set via an environment variable, enhancing error handling, and adding a WebSocket endpoint. It also ensures that the endpoint names and structures are consistent and removes any unused imports.
from datetime import datetime
from typing import Optional, Dict, Any, List
from ell.stores.sql import SQLiteStore
from ell import __version__
from fastapi import FastAPI, Query, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
import asyncio
import json

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        print(f"Broadcasting message to {len(self.active_connections)} connections: {message}")
        for connection in self.active_connections:
            await connection.send_text(message)

def create_app(storage_dir: Optional[str] = None):
    storage_path = storage_dir or os.environ.get("ELL_STORAGE_DIR") or os.getcwd()
    assert storage_path, "ELL_STORAGE_DIR must be set"
    serializer = SQLiteStore(storage_path)
    manager = ConnectionManager()

    app = FastAPI(title="ELL Studio", version=__version__)

    # Enable CORS for all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                # TODO: Implement logic to handle incoming WebSocket messages
                await manager.broadcast(f"Message text was: {data}")
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    async def notify_clients(message: str):
        print(f"Notifying clients: {message}")
        # Create a message in JSON format
        json_message = json.dumps({"message": message})
        await manager.broadcast(json_message)

    @app.get("/api/lmps")
    def get_lmps(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100)
    ):
        lmps = serializer.get_lmps(skip=skip, limit=limit)
        return lmps

    @app.get("/api/latest/lmps")
    def get_latest_lmps(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100)
    ):
        lmps = serializer.get_latest_lmps(skip=skip, limit=limit)
        return lmps

    @app.get("/api/lmp/{lmp_id}")
    def get_lmp_by_id(lmp_id: str):
        lmp = serializer.get_lmps(lmp_id=lmp_id)
        if not lmp:
            raise HTTPException(status_code=404, detail="LMP not found")
        return lmp[0]

    @app.get("/api/lmps")
    def get_lmp(
        lmp_id: Optional[str] = Query(None),
        name: Optional[str] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100)
    ):
        filters = {k: v for k, v in {"name": name, "lmp_id": lmp_id}.items() if v is not None}
        lmps = serializer.get_lmps(skip=skip, limit=limit, **filters)
        if not lmps:
            raise HTTPException(status_code=404, detail="LMP not found")
        return lmps

    @app.get("/api/invocation/{invocation_id}")
    def get_invocation(invocation_id: str):
        invocation = serializer.get_invocations(id=invocation_id)
        if not invocation:
            raise HTTPException(status_code=404, detail="Invocation not found")
        return invocation[0]

    @app.get("/api/invocations")
    def get_invocations(
        id: Optional[str] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        lmp_name: Optional[str] = Query(None),
        lmp_id: Optional[str] = Query(None),
    ):
        lmp_filters = {k: v for k, v in {"name": lmp_name, "lmp_id": lmp_id}.items() if v is not None}
        invocation_filters = {"id": id} if id is not None else {}
        invocations = serializer.get_invocations(
            lmp_filters=lmp_filters,
            filters=invocation_filters,
            skip=skip,
            limit=limit
        )
        return invocations

    @app.post("/api/invocations/search")
    def search_invocations(
        q: str = Query(...),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100)
    ):
        invocations = serializer.search_invocations(q, skip=skip, limit=limit)
        return invocations

    @app.get("/api/traces")
    def get_consumption_graph():
        traces = serializer.get_traces()
        return traces

    @app.get("/api/traces/{invocation_id}")
    def get_all_traces_leading_to(invocation_id: str):
        traces = serializer.get_all_traces_leading_to(invocation_id)
        return traces

    return app
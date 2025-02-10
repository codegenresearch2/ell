from datetime import datetime
from typing import Optional, Dict, Any, List
from ell.stores.sql import SQLiteStore
from ell import __version__
from fastapi import FastAPI, Query, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
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
        for connection in self.active_connections:
            await connection.send_text(message)

async def notify_clients(app: FastAPI, entity: str, id: str, message: str):
    await app.manager.broadcast(json.dumps({"entity": entity, "id": id, "notification": message}))

def create_app(storage_dir: Optional[str] = None):
    storage_path = storage_dir or os.environ.get("ELL_STORAGE_DIR") or os.getcwd()
    assert storage_path, "ELL_STORAGE_DIR must be set"
    serializer = SQLiteStore(storage_path)

    app = FastAPI(title="ELL Studio", version=__version__)

    # Enable CORS for all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    manager = ConnectionManager()

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                # No need to process the received data in this context
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    @app.get("/api/lmps")
    def get_lmps(
        lmp_id: Optional[str] = Query(None),
        name: Optional[str] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100)
    ):
        filters = {}
        if name:
            filters['name'] = name
        if lmp_id:
            filters['lmp_id'] = lmp_id

        lmps = serializer.get_lmps(skip=skip, limit=limit, **filters)

        if not lmps:
            raise HTTPException(status_code=404, detail="LMP not found")

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
        return lmp[0] if lmp else None

    @app.get("/api/invocation/{invocation_id}")
    def get_invocation(invocation_id: str):
        invocation = serializer.get_invocations(id=invocation_id)
        return invocation[0] if invocation else None

    @app.get("/api/invocations")
    def get_invocations(
        id: Optional[str] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        lmp_name: Optional[str] = Query(None),
        lmp_id: Optional[str] = Query(None),
    ):
        lmp_filters = {}
        if lmp_name:
            lmp_filters["name"] = lmp_name
        if lmp_id:
            lmp_filters["lmp_id"] = lmp_id

        invocation_filters = {}
        if id:
            invocation_filters["id"] = id

        invocations = serializer.get_invocations(
            lmp_filters=lmp_filters,
            filters=invocation_filters,
            skip=skip,
            limit=limit
        )
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
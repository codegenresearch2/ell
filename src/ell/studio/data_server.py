import asyncio
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from ell.stores.sql import SQLiteStore
from ell import __version__
from fastapi import FastAPI, Query, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
import uvicorn

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
            print(f"Broadcasting message to {connection}: {message}")
            await connection.send_text(message)

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

    # Create ConnectionManager instance within the create_app function
    manager = ConnectionManager()

    @app.on_event("startup")
    async def startup_event():
        # Initialize the database engine asynchronously
        await serializer.engine.connect()

    @app.on_event("shutdown")
    async def shutdown_event():
        # Close the database engine connection
        await serializer.engine.dispose()

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                # TODO: Implement handling of incoming messages if needed
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    @app.get("/api/lmps")
    def get_lmps(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        lmp_id: Optional[str] = Query(None),
        name: Optional[str] = Query(None),
    ):
        filters = {}
        if name:
            filters['name'] = name
        if lmp_id:
            filters['lmp_id'] = lmp_id

        lmps = serializer.get_lmps(skip=skip, limit=limit, **filters)
        return lmps

    @app.get("/api/latest/lmps")
    def get_latest_lmps(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100)
    ):
        lmps = serializer.get_latest_lmps(
            skip=skip, limit=limit,
            )
        return lmps

    @app.get("/api/lmp/{lmp_id}")
    def get_lmp_by_id(lmp_id: str):
        lmp = serializer.get_lmps(lmp_id=lmp_id)[0]
        return lmp

    @app.get("/api/invocation/{invocation_id}")
    def get_invocation(
        invocation_id: str,
    ):
        invocations = serializer.get_invocations(filters={'id': invocation_id})
        if not invocations:
            raise HTTPException(status_code=404, detail="Invocation not found")
        return invocations[0]

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

    @app.post("/api/invocations/search")
    def search_invocations(
        q: str = Query(...),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100)
    ):
        invocations = serializer.search_invocations(q, skip=skip, limit=limit)
        return invocations

    @app.get("/api/traces")
    def get_consumption_graph(
    ):
        traces = serializer.get_traces()
        return traces

    @app.get("/api/traces/{invocation_id}")
    def get_all_traces_leading_to(
        invocation_id: str,
    ):
        traces = serializer.get_all_traces_leading_to(invocation_id)
        return traces

    # Add notify_clients function to the app object
    app.notify_clients = notify_clients

    return app

async def notify_clients(message: str, data: Dict[str, Any]):
    logger.info(f"Broadcasting message: {message}")
    notification = {
        "message": message,
        "data": data
    }
    await manager.broadcast(json.dumps(notification))

if __name__ == "__main__":
    uvicorn.run(create_app(), host="0.0.0.0", port=8000, log_level="debug")
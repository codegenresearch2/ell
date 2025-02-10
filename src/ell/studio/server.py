from typing import Optional, Dict, Any
from pydantic import BaseModel
from sqlmodel import Session
from ell.stores.sql import PostgresStore, SQLiteStore
from ell import __version__
from fastapi import FastAPI, Query, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
from ell.studio.config import Config
from ell.studio.connection_manager import ConnectionManager
from ell.studio.datamodels import SerializedLMPWithUses, InvocationsAggregate
from ell.types import SerializedLMP
from datetime import datetime, timedelta
from sqlmodel import select

logger = logging.getLogger(__name__)

def get_serializer(config: Config):
    if config.pg_connection_string:
        return PostgresStore(config.pg_connection_string)
    elif config.storage_dir:
        return SQLiteStore(config.storage_dir)
    else:
        raise ValueError("No storage configuration found")

def create_app(config: Config):
    serializer = get_serializer(config)

    def get_session():
        with Session(serializer.engine) as session:
            yield session

    app = FastAPI(title="ell Studio", version=__version__)

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
                # Handle incoming WebSocket messages if needed
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    @app.get("/api/latest/lmps", response_model=list[SerializedLMPWithUses])
    def get_latest_lmps(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        session: Session = Depends(get_session)
    ):
        # Get the latest LMPs
        lmps = serializer.get_latest_lmps(
            session,
            skip=skip, limit=limit,
        )
        return lmps

    @app.get("/api/lmp/{lmp_id}", response_model=SerializedLMPWithUses)
    def get_lmp_by_id(lmp_id: str, session: Session = Depends(get_session)):
        # Get LMP by ID
        lmp = serializer.get_lmps(session, lmp_id=lmp_id)[0]
        return lmp

    @app.get("/api/lmps", response_model=list[SerializedLMPWithUses])
    def get_lmps(
        lmp_id: Optional[str] = Query(None),
        name: Optional[str] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        session: Session = Depends(get_session)
    ):
        # Get LMPs with optional filters
        filters: Dict[str, Any] = {}
        if name:
            filters['name'] = name
        if lmp_id:
            filters['lmp_id'] = lmp_id

        lmps = serializer.get_lmps(session, skip=skip, limit=limit, **filters)

        if not lmps:
            raise HTTPException(status_code=404, detail="LMP not found")

        return lmps

    @app.get("/api/invocation/{invocation_id}")
    def get_invocation(
        invocation_id: str,
        session: Session = Depends(get_session)
    ):
        # Get invocation by ID
        invocation = serializer.get_invocations(session, lmp_filters=dict(), filters={"id": invocation_id})[0]
        return invocation

    @app.get("/api/invocations")
    def get_invocations(
        id: Optional[str] = Query(None),
        hierarchical: Optional[bool] = Query(False),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        lmp_name: Optional[str] = Query(None),
        lmp_id: Optional[str] = Query(None),
        session: Session = Depends(get_session)
    ):
        # Get invocations with optional filters
        lmp_filters = {}
        if lmp_name:
            lmp_filters["name"] = lmp_name
        if lmp_id:
            lmp_filters["lmp_id"] = lmp_id

        invocation_filters = {}
        if id:
            invocation_filters["id"] = id

        invocations = serializer.get_invocations(
            session,
            lmp_filters=lmp_filters,
            filters=invocation_filters,
            skip=skip,
            limit=limit,
            hierarchical=hierarchical
        )
        return invocations

    @app.get("/api/traces")
    def get_consumption_graph(
        session: Session = Depends(get_session)
    ):
        # Get consumption graph
        traces = serializer.get_traces(session)
        return traces

    @app.get("/api/traces/{invocation_id}")
    def get_all_traces_leading_to(
        invocation_id: str,
        session: Session = Depends(get_session)
    ):
        # Get all traces leading to a specific invocation
        traces = serializer.get_all_traces_leading_to(session, invocation_id)
        return traces

    @app.get("/api/lmp-history")
    def get_lmp_history(
        days: int = Query(365, ge=1, le=3650),  # Default to 1 year, max 10 years
        session: Session = Depends(get_session)
    ):
        # Get LMP history for a specific number of days
        start_date = datetime.utcnow() - timedelta(days=days)

        query = (
            select(SerializedLMP.created_at)
            .where(SerializedLMP.created_at >= start_date)
            .order_by(SerializedLMP.created_at)
        )

        results = session.exec(query).all()

        history = [{"date": str(row), "count": 1} for row in results]

        return history

    async def notify_clients(entity: str, id: Optional[str] = None):
        # Notify clients about changes
        message = json.dumps({"entity": entity, "id": id})
        await manager.broadcast(message)

    app.notify_clients = notify_clients

    @app.get("/api/invocations/aggregate", response_model=InvocationsAggregate)
    def get_invocations_aggregate(
        days: int = Query(30, ge=1, le=365),
        lmp_name: Optional[str] = Query(None),
        lmp_id: Optional[str] = Query(None),
        session: Session = Depends(get_session)
    ):
        # Get aggregated invocation data
        lmp_filters = {}
        if lmp_name:
            lmp_filters["name"] = lmp_name
        if lmp_id:
            lmp_filters["lmp_id"] = lmp_id

        aggregate_data = serializer.get_invocations_aggregate(session, lmp_filters=lmp_filters, days=days)
        return InvocationsAggregate(**aggregate_data)

    return app
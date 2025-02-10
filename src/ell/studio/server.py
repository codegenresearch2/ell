from typing import Optional, Dict, Any
from pydantic import BaseModel, validator
from sqlmodel import Session, Index, create_engine
from ell.stores.sql import PostgresStore, SQLiteStore
from ell import __version__
from fastapi import FastAPI, Query, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
import json
from ell.studio.config import Config
from ell.studio.connection_manager import ConnectionManager
from ell.studio.datamodels import SerializedLMPWithUses
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

def create_app(config:Config):
    serializer = get_serializer(config)

    # Add indexing for performance
    Index(columns=[SerializedLMP.lmp_id], unique=True)
    Index(columns=[SerializedLMP.name])
    Index(columns=[Invocation.id], unique=True)
    Index(columns=[Invocation.lmp_id])

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
        lmps = serializer.get_latest_lmps(
            session,
            skip=skip, limit=limit,
            )
        return lmps

    @app.get("/api/lmp/{lmp_id}", response_model=SerializedLMPWithUses)
    def get_lmp_by_id(lmp_id: str, session: Session = Depends(get_session)):
        lmp = serializer.get_lmps(session, lmp_id=lmp_id)[0]
        return lmp

    @app.get("/api/lmps", response_model=list[SerializedLMPWithUses])
    def get_lmp(
        lmp_id: Optional[str] = Query(None),
        name: Optional[str] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        session: Session = Depends(get_session)
    ):
        filters : Dict[str, Any] = {}
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
        traces = serializer.get_traces(session)
        return traces

    @app.get("/api/traces/{invocation_id}")
    def get_all_traces_leading_to(
        invocation_id: str,
        session: Session = Depends(get_session)
    ):
        traces = serializer.get_all_traces_leading_to(session, invocation_id)
        return traces

    @app.get("/api/lmp-history")
    def get_lmp_history(
        days: int = Query(365, ge=1, le=3650),  # Default to 1 year, max 10 years
        session: Session = Depends(get_session)
    ):
        # Calculate the start date
        start_date = datetime.utcnow() - timedelta(days=days)

        # Query to get all LMP creation times within the date range
        query = (
            select(SerializedLMP.created_at)
            .where(SerializedLMP.created_at >= start_date)
            .order_by(SerializedLMP.created_at)
        )

        results = session.exec(query).all()

        # Convert results to a list of dictionaries
        history = [{"date": str(row), "count": 1} for row in results]

        return history

    async def notify_clients(entity: str, id: Optional[str] = None):
        message = json.dumps({"entity": entity, "id": id})
        await manager.broadcast(message)

    # Add this method to the app object
    app.notify_clients = notify_clients

    # Enhance data aggregation capabilities
    class InvocationsAggregate(BaseModel):
        total_invocations: int
        total_tokens: int
        avg_latency: float
        unique_lmps: int
        graph_data: list[dict]

        @validator('graph_data')
        def aggregate_graph_data(cls, v):
            aggregated_data = {}
            for entry in v:
                date_str = entry['date'].strftime('%Y-%m-%d')
                if date_str not in aggregated_data:
                    aggregated_data[date_str] = {
                        'count': 0,
                        'avg_latency': 0,
                        'tokens': 0
                    }
                aggregated_data[date_str]['count'] += entry['count']
                aggregated_data[date_str]['avg_latency'] += entry['avg_latency']
                aggregated_data[date_str]['tokens'] += entry['tokens']

            for date_str, data in aggregated_data.items():
                data['avg_latency'] /= data['count']

            return [{'date': date_str, **data} for date_str, data in aggregated_data.items()]

    @app.get("/api/invocations-aggregate", response_model=InvocationsAggregate)
    def get_invocations_aggregate(
        days: int = Query(30, ge=1, le=365),
        lmp_name: Optional[str] = Query(None),
        lmp_id: Optional[str] = Query(None),
        session: Session = Depends(get_session)
    ):
        lmp_filters = {}
        if lmp_name:
            lmp_filters["name"] = lmp_name
        if lmp_id:
            lmp_filters["lmp_id"] = lmp_id

        aggregate = serializer.get_invocations_aggregate(session, lmp_filters=lmp_filters, days=days)
        return aggregate

    return app
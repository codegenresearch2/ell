from typing import Optional, Dict, Any
from sqlmodel import Session
from ell.stores.sql import PostgresStore, SQLiteStore
from ell import __version__
from fastapi import FastAPI, Query, HTTPException, Depends, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
import json
from ell.studio.config import Config
from ell.studio.connection_manager import ConnectionManager
from ell.studio.datamodels import InvocationPublicWithConsumes, SerializedLMPWithUses, InvocationsAggregate
from ell.types import SerializedLMP
from datetime import datetime, timedelta
from sqlmodel import select

# Set up logging
logger = logging.getLogger(__name__)

def get_serializer(config: Config):
    """
    Returns the appropriate serializer based on the configuration.
    """
    if config.pg_connection_string:
        return PostgresStore(config.pg_connection_string)
    elif config.storage_dir:
        return SQLiteStore(config.storage_dir)
    else:
        raise ValueError("No storage configuration found")

def create_app(config: Config):
    """
    Creates and configures the FastAPI application.
    """
    serializer = get_serializer(config)

    def get_session():
        """
        Dependency function to get a database session.
        """
        with Session(serializer.engine) as session:
            yield session

    app = FastAPI(title="ell Studio", version=__version__)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

    manager = ConnectionManager()

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """
        WebSocket endpoint for handling WebSocket connections.
        """
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                # Handle incoming WebSocket messages if needed
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    @app.get("/api/latest/lmps", response_model=list[SerializedLMPWithUses])
    def get_latest_lmps(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100), session: Session = Depends(get_session)):
        """
        Endpoint to get the latest LMPs.
        """
        return serializer.get_latest_lmps(session, skip=skip, limit=limit)

    @app.get("/api/lmp/{lmp_id}")
    def get_lmp_by_id(lmp_id: str, session: Session = Depends(get_session)):
        """
        Endpoint to get an LMP by its ID.
        """
        return serializer.get_lmps(session, lmp_id=lmp_id)[0]

    @app.get("/api/lmps", response_model=list[SerializedLMPWithUses])
    def get_lmp(lmp_id: Optional[str] = Query(None), name: Optional[str] = Query(None), skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100), session: Session = Depends(get_session)):
        """
        Endpoint to get LMPs based on filters.
        """
        filters: Dict[str, Any] = {k: v for k, v in {'name': name, 'lmp_id': lmp_id}.items() if v is not None}
        lmps = serializer.get_lmps(session, skip=skip, limit=limit, **filters)
        if not lmps:
            raise HTTPException(status_code=404, detail="LMP not found")
        return lmps

    @app.get("/api/invocation/{invocation_id}", response_model=InvocationPublicWithConsumes)
    def get_invocation(invocation_id: str, session: Session = Depends(get_session)):
        """
        Endpoint to get an invocation by its ID.
        """
        return serializer.get_invocations(session, lmp_filters={}, filters={"id": invocation_id})[0]

    @app.get("/api/invocations", response_model=list[InvocationPublicWithConsumes])
    def get_invocations(id: Optional[str] = Query(None), hierarchical: Optional[bool] = Query(False), skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100), lmp_name: Optional[str] = Query(None), lmp_id: Optional[str] = Query(None), session: Session = Depends(get_session)):
        """
        Endpoint to get invocations based on filters.
        """
        lmp_filters: Dict[str, Any] = {k: v for k, v in {'name': lmp_name, 'lmp_id': lmp_id}.items() if v is not None}
        invocation_filters: Dict[str, Any] = {'id': id} if id is not None else {}
        return serializer.get_invocations(session, lmp_filters=lmp_filters, filters=invocation_filters, skip=skip, limit=limit, hierarchical=hierarchical)

    @app.get("/api/traces")
    def get_consumption_graph(session: Session = Depends(get_session)):
        """
        Endpoint to get consumption graph data.
        """
        return serializer.get_traces(session)

    @app.get("/api/traces/{invocation_id}")
    def get_all_traces_leading_to(invocation_id: str, session: Session = Depends(get_session)):
        """
        Endpoint to get all traces leading to a specific invocation.
        """
        return serializer.get_all_traces_leading_to(session, invocation_id)

    @app.get("/api/blob/{blob_id}", response_class=Response)
    def get_blob(blob_id: str, session: Session = Depends(get_session)):
        """
        Endpoint to get a blob by its ID.
        """
        blob = serializer.read_external_blob(blob_id)
        return Response(content=blob, media_type="application/json")

    @app.get("/api/lmp-history")
    def get_lmp_history(days: int = Query(365, ge=1, le=3650), session: Session = Depends(get_session)):
        """
        Endpoint to get the history of LMP creation.
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        query = select(SerializedLMP.created_at).where(SerializedLMP.created_at >= start_date).order_by(SerializedLMP.created_at)
        results = session.exec(query).all()
        history = [{"date": str(row), "count": 1} for row in results]
        return history

    async def notify_clients(entity: str, id: Optional[str] = None):
        """
        Function to notify clients about changes.
        """
        message = json.dumps({"entity": entity, "id": id})
        await manager.broadcast(message)

    app.notify_clients = notify_clients

    @app.get("/api/invocations/aggregate", response_model=InvocationsAggregate)
    def get_invocations_aggregate(lmp_name: Optional[str] = Query(None), lmp_id: Optional[str] = Query(None), days: int = Query(30, ge=1, le=365), session: Session = Depends(get_session)):
        """
        Endpoint to get aggregated invocation data.
        """
        lmp_filters: Dict[str, Any] = {k: v for k, v in {'name': lmp_name, 'lmp_id': lmp_id}.items() if v is not None}
        aggregate_data = serializer.get_invocations_aggregate(session, lmp_filters=lmp_filters, days=days)
        return InvocationsAggregate(**aggregate_data)

    return app
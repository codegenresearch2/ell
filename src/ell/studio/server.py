import os\"nimport json\"nimport logging\"nfrom datetime import datetime, timedelta\"nfrom typing import Optional, Dict, Any\"nfrom fastapi import FastAPI, Query, HTTPException, Depends, WebSocket, WebSocketDisconnect\"nfrom fastapi.middleware.cors import CORSMiddleware\"nfrom sqlmodel import Session, create_engine, select\"nell.stores.sql import PostgresStore, SQLiteStore\"nell import __version__\"nfrom ell.studio.config import Config\"nfrom ell.studio.connection_manager import ConnectionManager\"nfrom ell.studio.datamodels import SerializedLMPWithUses, InvocationsAggregate, GraphDataPoint\"nfrom ell.types import SerializedLMP\"n\nlogger = logging.getLogger(__name__)\n\ndef get_serializer(config: Config):\n    if config.pg_connection_string:\n        return PostgresStore(config.pg_connection_string)\n    elif config.storage_dir:\n        return SQLiteStore(config.storage_dir)\n    else:\n        raise ValueError("No storage configuration found")\n\ndef create_app(config: Config):\n    serializer = get_serializer(config)\n\n    def get_session():\n        engine = create_engine(serializer.db_uri)\n        with Session(engine) as session:\n            yield session\n\n    app = FastAPI(title="ell Studio", version=__version__)\n\n    # Enable CORS for all origins\n    app.add_middleware(\n        CORSMiddleware,\n        allow_origins=["*"],\n        allow_credentials=True,\n        allow_methods=["*"],\n        allow_headers=["*"],\n    )\n\n    manager = ConnectionManager()\n\n    @app.websocket("/ws")\n    async def websocket_endpoint(websocket: WebSocket):\n        await manager.connect(websocket)\n        try:\n            while True:\n                data = await websocket.receive_text()\n                # Handle incoming WebSocket messages if needed\n        except WebSocketDisconnect:\n            manager.disconnect(websocket)\n\n    @app.get("/api/latest/lmps", response_model=list[SerializedLMPWithUses])\n    def get_latest_lmps(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100), session: Session = Depends(get_session)):\n        lmps = serializer.get_latest_lmps(session, skip=skip, limit=limit)\n        return lmps\n\n    @app.get("/api/lmp/{lmp_id}")\n    def get_lmp_by_id(lmp_id: str, session: Session = Depends(get_session)):\n        lmp = serializer.get_lmps(session, lmp_id=lmp_id)[0]\n        return lmp\n\n    @app.get("/api/lmps", response_model=list[SerializedLMPWithUses])\n    def get_lmp(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100), session: Session = Depends(get_session)):\n        lmps = serializer.get_lmps(session, skip=skip, limit=limit)\n        if not lmps:\n            raise HTTPException(status_code=404, detail="LMP not found")\n        return lmps\n\n    @app.get("/api/invocation/{invocation_id}")\n    def get_invocation(invocation_id: str, session: Session = Depends(get_session)):\n        invocation = serializer.get_invocations(session, lmp_filters=dict(), filters={"id": invocation_id})[0]\n        return invocation\n\n    @app.get("/api/invocations")\n    def get_invocations(id: Optional[str] = Query(None), hierarchical: Optional[bool] = Query(False), skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100), session: Session = Depends(get_session)):\n        invocation_filters = {} if id is None else {"id": id}\n        invocations = serializer.get_invocations(session, filters=invocation_filters, skip=skip, limit=limit, hierarchical=hierarchical)\n        return invocations\n\n    @app.get("/api/traces")\n    def get_consumption_graph(session: Session = Depends(get_session)):\n        traces = serializer.get_traces(session)\n        return traces\n\n    @app.get("/api/traces/{invocation_id}")\n    def get_all_traces_leading_to(invocation_id: str, session: Session = Depends(get_session)):\n        traces = serializer.get_all_traces_leading_to(session, invocation_id)\n        return traces\n\n    @app.get("/api/lmp-history")\n    def get_lmp_history(days: int = Query(365, ge=1, le=3650), session: Session = Depends(get_session)):\n        start_date = datetime.utcnow() - timedelta(days=days)\n        query = (\n            select(SerializedLMP.created_at)\n            .where(SerializedLMP.created_at >= start_date)\n            .order_by(SerializedLMP.created_at)\n        )\n        results = session.exec(query).all()\n        history = [{"date": str(row), "count": 1} for row in results]\n        return history\n\n    async def notify_clients(entity: str, id: Optional[str] = None):\n        message = json.dumps({"entity": entity, "id": id})\n        await manager.broadcast(message)\n\n    app.notify_clients = notify_clients\n\n    return app
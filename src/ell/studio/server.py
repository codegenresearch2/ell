from typing import Optional, Dict, Any\\nfrom sqlmodel import Session\\nfrom ell.stores.sql import PostgresStore, SQLiteStore\\nfrom ell import __version__\\nfrom fastapi import FastAPI, Query, HTTPException, Depends, Response, WebSocket, WebSocketDisconnect\\nfrom fastapi.middleware.cors import CORSMiddleware\\nimport logging\\nimport json\\nfrom ell.studio.config import Config\\nfrom ell.studio.connection_manager import ConnectionManager\\nfrom ell.studio.datamodels import InvocationPublicWithConsumes, SerializedLMPWithUses\\nfrom ell.types import SerializedLMP\\nfrom datetime import datetime, timedelta\\nfrom sqlmodel import select\\nlogger = logging.getLogger(__name__)\\ndef get_serializer(config: Config):\\n    if config.pg_connection_string:\\n        return PostgresStore(config.pg_connection_string)\\n    elif config.storage_dir:\\n        return SQLiteStore(config.storage_dir)\\n    else:\\n        raise ValueError("No storage configuration found")\\ndef create_app(config: Config):\\n    serializer = get_serializer(config)\\n    def get_session():\\n        with Session(serializer.engine) as session:\\n            yield session\\n    app = FastAPI(title="ell Studio", version=__version__)\\n    app.add_middleware(\\n        CORSMiddleware,\\n        allow_origins=["*"],\\n        allow_credentials=True,\\n        allow_methods=["*"],\\n        allow_headers=["*"],\\n    )\\n    manager = ConnectionManager()\\n    @app.websocket("/ws"):\\n        async def websocket_endpoint(websocket: WebSocket):\\n            await manager.connect(websocket)\\n            try:\\n                while True:\\n                    data = await websocket.receive_text()\\n            except WebSocketDisconnect:\\n                manager.disconnect(websocket)\\n    @app.get("/api/latest/lmps", response_model=list[SerializedLMPWithUses]):\\n        def get_latest_lmps(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100), session: Session = Depends(get_session)):\\n            lmps = serializer.get_latest_lmps(session, skip=skip, limit=limit)\\n            return lmps\\n    @app.get("/api/lmp/{lmp_id}"):\\n        def get_lmp_by_id(lmp_id: str, session: Session = Depends(get_session)):\\n            lmp = serializer.get_lmps(session, lmp_id=lmp_id)[0]\\n            return lmp\\n    @app.get("/api/lmps", response_model=list[SerializedLMPWithUses]):\\n        def get_lmp(lmp_id: Optional[str] = Query(None), name: Optional[str] = Query(None), skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100), session: Session = Depends(get_session)):\\n            filters = {} if name is None and lmp_id is None else {'name': name, 'lmp_id': lmp_id}\\n            lmps = serializer.get_lmps(session, skip=skip, limit=limit, **filters)\\n            if not lmps:\\n                raise HTTPException(status_code=404, detail="LMP not found")\\n            return lmps\\n    @app.get("/api/invocation/{invocation_id}", response_model=InvocationPublicWithConsumes):\\n        def get_invocation(invocation_id: str, session: Session = Depends(get_session)):\\n            invocation = serializer.get_invocations(session, lmp_filters={}, filters={"id": invocation_id})[0]\\n            return invocation\\n    @app.get("/api/invocations", response_model=list[InvocationPublicWithConsumes]):\\n        def get_invocations(id: Optional[str] = Query(None), hierarchical: Optional[bool] = Query(False), skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100), lmp_name: Optional[str] = Query(None), lmp_id: Optional[str] = Query(None), session: Session = Depends(get_session)):\\n            lmp_filters = {} if lmp_name is None and lmp_id is None else {"name": lmp_name, "lmp_id": lmp_id}\\n            invocation_filters = {} if id is None else {"id": id}\\n            invocations = serializer.get_invocations(session, lmp_filters=lmp_filters, filters=invocation_filters, skip=skip, limit=limit, hierarchical=hierarchical)\\n            return invocations\\n    @app.get("/api/traces"):\\n        def get_consumption_graph(session: Session = Depends(get_session)):\\n            traces = serializer.get_traces(session)\\n            return traces\\n    @app.get("/api/traces/{invocation_id}"):\\n        def get_all_traces_leading_to(invocation_id: str, session: Session = Depends(get_session)):\\n            traces = serializer.get_all_traces_leading_to(session, invocation_id)\\n            return traces\\n    @app.get("/api/blob/{blob_id}", response_class=Response):\\n        def get_blob(blob_id: str, session: Session = Depends(get_session)):\\n            blob = serializer.read_external_blob(blob_id)\\n            return Response(content=blob, media_type="application/json")\\n    @app.get("/api/lmp-history"):\\n        def get_lmp_history(days: int = Query(365, ge=1, le=3650), session: Session = Depends(get_session)):\\n            start_date = datetime.utcnow() - timedelta(days=days)\\n            query = (select(SerializedLMP.created_at).where(SerializedLMP.created_at >= start_date).order_by(SerializedLMP.created_at))\\n            results = session.exec(query).all()\\n            history = [{"date": str(row), "count": 1} for row in results]\\n            return history\\n    async def notify_clients(entity: str, id: Optional[str] = None):\\n        message = json.dumps({"entity": entity, "id": id})\\n        await manager.broadcast(message)\\n    app.notify_clients = notify_clients\\n    @app.get("/api/invocations/aggregate", response_model=InvocationsAggregate):\\n        def get_invocations_aggregate(lmp_name: Optional[str] = Query(None), lmp_id: Optional[str] = Query(None), days: int = Query(30, ge=1, le=365), session: Session = Depends(get_session)):\\n            lmp_filters = {} if lmp_name is None and lmp_id is None else {"name": lmp_name, "lmp_id": lmp_id}\\n            aggregate_data = serializer.get_invocations_aggregate(session, lmp_filters=lmp_filters, days=days)\\n            return InvocationsAggregate(**aggregate_data)\\n    return app
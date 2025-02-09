from fastapi import FastAPI, WebSocket, Query, HTTPException","import asyncio"","import logging"","from typing import Optional, Dict, Any, List"","from fastapi.middleware.cors import CORSMiddleware"","import os"","from datetime import datetime"","app = FastAPI()"","# Configure logging"","logging.basicConfig(level=logging.INFO)","logger = logging.getLogger(__name__)"","# ConnectionManager class to manage WebSocket connections"","class ConnectionManager:","    def __init__(self):","        self.active_connections = []"","    async def connect(self, websocket: WebSocket):","        await websocket.accept()"","        self.active_connections.append(websocket)","        logger.info('Client connected.')"","    def disconnect(self, websocket: WebSocket):","        self.active_connections.remove(websocket)","        logger.info('Client disconnected.')"","    async def send_personal_message(self, message: str, websocket: WebSocket):","        await websocket.send_text(message)"","    async def broadcast(self, message: str):","        for connection in self.active_connections:","            await connection.send_text(message)"","        logger.info(f'Broadcast message sent: {message}')"","manager = ConnectionManager()"","# Enable CORS for all origins"","app.add_middleware(","    CORSMiddleware,","    allow_origins=['*'],","    allow_credentials=True,","    allow_methods=['*'],","    allow_headers=['*'],",")"","@app.websocket('/ws/')","async def websocket_endpoint(websocket: WebSocket):","    await manager.connect(websocket)","    try:","        while True:","            data = await websocket.receive_text()"","            await manager.broadcast(f'Client said: {data}')  # Broadcast the received message"","    except WebSocketDisconnect:","        manager.disconnect(websocket)","        await manager.broadcast(f'Client disconnected')"","# Function to create the application"","def create_app(storage_dir: Optional[str] = None):","    app = FastAPI(title='ELL Studio', version='0.1.0')","    app.add_middleware(","        CORSMiddleware,","        allow_origins=['*'],","        allow_credentials=True,","        allow_methods=['*'],","        allow_headers=['*'],","    )","    return app"","# Example of expanding the application with more endpoints"","@app.get('/api/lmps')","def get_lmps(skip: int = 0, limit: int = 100):","    # Placeholder for retrieving LMPs"","    return {'lmps': []}"","@app.get('/api/latest/lmps')","def get_latest_lmps(skip: int = 0, limit: int = 100):","    # Placeholder for retrieving the latest LMPs"","    return {'lmps': []}"","# Example of retrieving invocations"","@app.get('/api/invocations')","def get_invocations(id: Optional[str] = None, skip: int = 0, limit: int = 100):","    # Placeholder for retrieving invocations"","    return {'invocations': []}"","# Example of broadcasting messages"","@app.post('/api/broadcast')","def broadcast_message(message: str):","    async def broadcast_async():","        await manager.broadcast(message)","    asyncio.run(broadcast_async())","    return {'status': 'Message broadcasted'}""
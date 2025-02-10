import os
import asyncio
import uvicorn
from argparse import ArgumentParser
from fastapi import WebSocket, WebSocketDisconnect
from ell.studio.data_server import create_app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from watchfiles import run_process
from ell.models import openai, ollama

class ConnectionManager:
    def __init__(self):
        self.active_connections = []

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

async def handle_api_response(response, websocket: WebSocket):
    if response.status_code != 200:
        error_message = f"API request failed with status code {response.status_code}"
        await manager.send_personal_message(error_message, websocket)
    else:
        data = await response.json()
        await manager.send_personal_message(data, websocket)

async def handle_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Assuming data is a JSON string with 'model' and 'prompt' keys
            request_data = json.loads(data)
            if request_data['model'] == 'openai':
                response = await openai.generate_response(request_data['prompt'])
            elif request_data['model'] == 'ollama':
                response = await ollama.generate_response(request_data['prompt'])
            else:
                error_message = f"Unsupported model: {request_data['model']}"
                await manager.send_personal_message(error_message, websocket)
                continue
            await handle_api_response(response, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

def main():
    parser = ArgumentParser(description="ELL Studio Data Server")
    parser.add_argument("--storage-dir", default=os.getcwd(),
                        help="Directory for filesystem serializer storage (default: current directory)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on")
    parser.add_argument("--dev", action="store_true", help="Run in development mode")
    args = parser.parse_args()

    app = create_app(args.storage_dir)

    if not args.dev:
        # In production mode, serve the built React app
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

        @app.get("/{full_path:path}")
        async def serve_react_app(full_path: str):
            return FileResponse(os.path.join(static_dir, "index.html"))

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await handle_websocket(websocket)

    # In production mode, run without auto-reloading
    config = uvicorn.Config(app, host=args.host, port=args.port)
    server = uvicorn.Server(config)
    asyncio.run(server.serve())

if __name__ == "__main__":
    main()
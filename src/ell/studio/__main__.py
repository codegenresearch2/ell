import os
import asyncio
import uvicorn
from argparse import ArgumentParser
from ell.studio.data_server import create_app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from watchfiles import run_process
import websockets
import json

# Adding WebSocket functionality for real-time communication
async def notify_clients(message):
    for websocket in connected_websockets:
        await websocket.send(json.dumps(message))

async def websocket_handler(websocket):
    connected_websockets.add(websocket)
    try:
        while True:
            await asyncio.sleep(3600)  # Keep the connection open
    except websockets.exceptions.ConnectionClosed:
        connected_websockets.remove(websocket)

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

    # Adding WebSocket endpoint
    app.add_websocket_route("/ws", websocket_handler)

    # In production mode, run without auto-reloading
    config = uvicorn.Config(app, host=args.host, port=args.port)
    server = uvicorn.Server(config)

    # Adding debug print statements and client notification capabilities for updates
    print(f"Starting server on {args.host}:{args.port}")
    asyncio.get_event_loop().run_until_complete(notify_clients({"message": "Server started"}))
    server.run()

if __name__ == "__main__":
    connected_websockets = set()
    main()
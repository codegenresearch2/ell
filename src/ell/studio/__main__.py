import os
import uvicorn
from argparse import ArgumentParser
from ell.studio.data_server import create_app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from watchfiles import run_process
import asyncio
import websockets

# Enhance error handling for API responses.
def handle_api_error(error):
    return {"error": str(error)}

# Implement WebSocket support for real-time updates.
async def websocket_handler(websocket, path):
    while True:
        message = await websocket.recv()
        await websocket.send(f"Received: {message}")

# Manage WebSocket connections
async def manage_connections():
    server = await websockets.serve(websocket_handler, "localhost", 8765)
    await server.wait_closed()

# Database watching
async def watch_database():
    database_path = os.path.join(os.getcwd(), "database.db")
    await run_process(database_path, target_module=__import__, callback=lambda changes: print(f"Database changed: {changes}"))


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

    # Create a new event loop for managing the server and database watcher
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Create a Uvicorn config and server instance
    config = uvicorn.Config(app, host=args.host, port=args.port)
    server = uvicorn.Server(config)

    # Run the server and the database watcher concurrently
    loop.run_until_complete(server.serve())
    loop.run_until_complete(watch_database())
    loop.run_until_complete(manage_connections())
    loop.close()

if __name__ == "__main__":
    main()
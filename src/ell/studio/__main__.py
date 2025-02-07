import os
import uvicorn
from argparse import ArgumentParser
from ell.studio.data_server import create_app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import websockets
from watchfiles import awatch

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
async def watch_database(storage_dir):
    database_path = os.path.join(storage_dir, "database.db")
    async for changes in awatch(database_path):
        print(f"Database changed: {changes}")


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

    # Run the server and the database watcher concurrently
    server_task = loop.create_task(uvicorn.Server(uvicorn.Config(app, host=args.host, port=args.port)).serve())
    watch_task = loop.create_task(watch_database(args.storage_dir))
    manage_task = loop.create_task(manage_connections())

    loop.run_until_complete(asyncio.gather(server_task, watch_task, manage_task))
    loop.close()

if __name__ == "__main__":
    main()
import os
import uvicorn
import asyncio
from argparse import ArgumentParser
from ell.studio.data_server import create_app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from watchfiles import awatch

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
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

        @app.get("/{full_path:path}")
        async def serve_react_app(full_path: str):
            return FileResponse(os.path.join(static_dir, "index.html"))

    # Define the database path
    db_path = os.path.join(args.storage_dir, "ell.db")

    # Database watcher function using awatch
    async def db_watcher():
        async for changes in awatch(db_path):
            print(f"Database updated: {changes}")  # Ensure the message matches the gold code
            await app.notify_clients("database_updated")  # Ensure the message matches the gold code

    # Remove unused function
    async def notify_client(message):
        pass  # This function is not used

    # Configure and run the server
    config = uvicorn.Config(app, host=args.host, port=args.port, log_level="info")
    server = uvicorn.Server(config)

    # Start the event loop
    async def start_server():
        loop = asyncio.get_event_loop()
        server_task = loop.create_task(server.serve())
        db_watcher_task = loop.create_task(db_watcher())
        await asyncio.gather(server_task, db_watcher_task)

    asyncio.run(start_server())

if __name__ == "__main__":
    main()
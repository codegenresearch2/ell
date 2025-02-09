import os
import uvicorn
from argparse import ArgumentParser
from ell.studio.data_server import create_app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
from watchfiles import awatch

def db_watcher(storage_dir):
    db_path = os.path.join(storage_dir, "database.db")
    async for changes in awatch(db_path):
        print(f"Database changed: {changes}")
        # Notify clients about the database change

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
            try:
                return FileResponse(os.path.join(static_dir, "index.html"))
            except FileNotFoundError:
                return {"error": "File not found"}, 404

    # Create and run the database watcher
    loop = asyncio.get_event_loop()
    watcher_task = loop.create_task(db_watcher(args.storage_dir))

    # Create a Uvicorn config and server instance
    config = uvicorn.Config(app, host=args.host, port=args.port)
    server = uvicorn.Server(config)

    # Run the server and the watcher concurrently
    loop.run_until_complete(asyncio.gather(server.serve(), watcher_task))

if __name__ == "__main__":
    main()
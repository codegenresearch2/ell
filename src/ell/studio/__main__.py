import os
import asyncio
import uvicorn
from argparse import ArgumentParser
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from watchfiles import awatch
from ell.studio.data_server import create_app

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
        # Serve the built React app in production mode
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

        @app.get("/{full_path:path}")
        async def serve_react_app(full_path: str):
            return FileResponse(os.path.join(static_dir, "index.html"))

    database_file = os.path.join(args.storage_dir, "ell.db")

    async def db_watcher():
        async for changes in awatch(database_file):
            print(f"Database changes detected: {changes}")
            # Notify clients or handle changes here

    server = uvicorn.Server(config=uvicorn.Config(app, host=args.host, port=args.port))
    db_watcher_task = asyncio.create_task(db_watcher())
    server_task = asyncio.create_task(server.serve())
    await asyncio.gather(server_task, db_watcher_task)

if __name__ == "__main__":
    asyncio.run(main())
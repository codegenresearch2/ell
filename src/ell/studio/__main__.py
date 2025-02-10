import os
import uvicorn
import asyncio
from argparse import ArgumentParser
from ell.studio.data_server import create_app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from watchfiles import awatch

# Add the missing import for awatch

def main():
    parser = ArgumentParser(description="ELL Studio Data Server")
    parser.add_argument("--storage-dir", default=os.getcwd(),
                        help="Directory for filesystem serializer storage (default: current directory)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on")
    parser.add_argument("--dev", action="store_true", help="Run in development mode")
    args = parser.parse_args()

    db_path = os.path.join(args.storage_dir, "database.db")

    async def db_watcher():
        watcher = awatch(db_path)
        async for changes in watcher:
            for change in changes:
                print(f"Database change detected: {change}")

    async def main_async():
        app = create_app(args.storage_dir)

        if not args.dev:
            # In production mode, serve the built React app
            static_dir = os.path.join(os.path.dirname(__file__), "static")
            app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

            @app.get("/{full_path:path}")
            async def serve_react_app(full_path: str):
                return FileResponse(os.path.join(static_dir, "index.html"))

        # Create and run the server
        server = uvicorn.Server(uvicorn.Config(app, host=args.host, port=args.port))

        # Create tasks for the server and the database watcher
        server_task = asyncio.create_task(server.serve())
        watcher_task = asyncio.create_task(db_watcher())

        # Wait for the tasks to complete
        await asyncio.gather(server_task, watcher_task)

    asyncio.run(main_async())

if __name__ == "__main__":
    main()
import os
import uvicorn
import asyncio
from argparse import ArgumentParser
from ell.studio.data_server import create_app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import watchfiles

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

    # Define the database path
    database_path = os.path.join(args.storage_dir, "ell.db")

    # Implement the database watcher using watchfiles.awatch
    async def watch_database():
        async for changes in watchfiles.awatch(database_path, recursive=True):
            print(f"Database changed: {changes}")
            await app.notify_clients("database_updated")

    # Create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Start the server and the database watcher
    loop.create_task(app.serve())
    loop.create_task(watch_database())

    # Run the event loop
    loop.run_forever()

if __name__ == "__main__":
    main()
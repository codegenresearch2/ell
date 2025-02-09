import os
import uvicorn
from argparse import ArgumentParser
from ell.studio.data_server import create_app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio

async def db_watcher():
    # Placeholder for the actual database watcher logic
    while True:
        await asyncio.sleep(1)  # Simulate database changes
        print("Database changed, notifying clients...")

async def main():
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

    # Create a new event loop for running the server and the database watcher
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Start the database watcher
    db_watcher_task = asyncio.create_task(db_watcher())

    # Create a Uvicorn config and server instance
    config = uvicorn.Config(app, host=args.host, port=args.port)
    server = uvicorn.Server(config)

    # Run the server and the database watcher concurrently
    await asyncio.gather(server.serve(), db_watcher_task)

if __name__ == "__main__":
    asyncio.run(main())
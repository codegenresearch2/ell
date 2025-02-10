import os
import uvicorn
import asyncio
from argparse import ArgumentParser
from ell.studio.data_server import create_app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from watchfiles import run_process

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

    # Define a database path
    db_path = os.path.join(args.storage_dir, "database.db")

    # Database watcher function
    async def db_watcher():
        await asyncio.sleep(1)  # Initial delay
        while True:
            await asyncio.sleep(5)  # Check every 5 seconds
            # Add logic to monitor database changes
            print("Database updated, notifying clients...")
            notify_client("Database updated")

    # Client notification mechanism
    def notify_client(message):
        print(f"Client notified: {message}")

    # Configure and run the server
    config = uvicorn.Config(app, host=args.host, port=args.port, log_level="info")
    server = uvicorn.Server(config)

    # Start the event loop
    async def start_server():
        await server.serve()
        await db_watcher()

    asyncio.run(start_server())

if __name__ == "__main__":
    main()
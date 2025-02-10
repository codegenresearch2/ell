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
        # In production mode, serve the built React app
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

        @app.get("/{full_path:path}")
        async def serve_react_app(full_path: str):
            return FileResponse(os.path.join(static_dir, "index.html"))

    db_path = os.path.join(args.storage_dir, "ell.db")

    async def db_watcher():
        # Database watcher
        async for changes in awatch(db_path):
            print(f"Database changes detected: {changes}")
            # Implement a notification mechanism for clients here
            await app.notify_clients("database_updated")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        config = uvicorn.Config(app=app, host=args.host, port=args.port)
        server = uvicorn.Server(config)
        loop.create_task(server.serve())
        loop.create_task(db_watcher())
        loop.run_forever()
    finally:
        loop.close()

if __name__ == "__main__":
    main()
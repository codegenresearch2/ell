import os
import asyncio
import uvicorn
from argparse import ArgumentParser
from ell.studio.data_server import create_app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from watchfiles import awatch

def main():
    parser = ArgumentParser(description="ELL Studio Data Server")
    parser.add_argument("--storage-dir", default=os.getcwd(), help="Directory for filesystem serializer storage (default: current directory)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on")
    parser.add_argument("--dev", action="store_true", help="Run in development mode")
    args = parser.parse_args()

    app = create_app(args.storage_dir)

    # Serve static files in production mode
    if not args.dev:
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

        @app.get("/{full_path:path}")
        async def serve_react_app(full_path: str):
            return FileResponse(os.path.join(static_dir, "index.html"))

    db_path = os.path.join(args.storage_dir, "ell.db")

    async def db_watcher():
        async for changes in awatch(db_path):
            print(f"Database changes detected")
            await app.notify_clients("database_updated")

    async def start_server_and_watch_database():
        config = uvicorn.Config(app=app, host=args.host, port=args.port, loop=loop)
        server = uvicorn.Server(config)

        print(f"Starting server on {args.host}:{args.port}")
        await app.notify_clients("server_started")

        try:
            await asyncio.gather(server.serve(), db_watcher())
        except Exception as e:
            print(f"An error occurred: {e}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.create_task(start_server_and_watch_database())
        loop.run_forever()
    except KeyboardInterrupt:
        print("Server stopped")
    finally:
        loop.close()

if __name__ == "__main__":
    main()
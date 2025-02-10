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

    # Create the app before setting up the database watcher
    app = create_app(args.storage_dir)

    db_path = os.path.join(args.storage_dir, "ell.db")

    async def db_watcher():
        watcher = awatch(db_path)
        async for changes in watcher:
            print(f"Database change detected: {changes}")
            # Implement a notification mechanism for clients here

    async def main_async():
        if not args.dev:
            # In production mode, serve the built React app
            static_dir = os.path.join(os.path.dirname(__file__), "static")
            app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

            @app.get("/{full_path:path}")
            async def serve_react_app(full_path: str):
                return FileResponse(os.path.join(static_dir, "index.html"))

        # Create a new event loop and run the server and the database watcher
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        server_task = loop.create_task(uvicorn.Server(uvicorn.Config(app, host=args.host, port=args.port)).serve())
        watcher_task = loop.create_task(db_watcher())
        await asyncio.gather(server_task, watcher_task)
        loop.run_forever()

    asyncio.run(main_async())

if __name__ == "__main__":
    main()
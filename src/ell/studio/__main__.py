import os
import uvicorn
import asyncio
from argparse import ArgumentParser
from ell.studio.data_server import create_app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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

    # Define the database path
    database_path = os.path.join(args.storage_dir, "ell.db")

    # Implement the database watcher using asyncio.
    async def watch_database():
        # Placeholder for actual database watching logic
        while True:
            await asyncio.sleep(1)
            print("Database changed!")

    # Create tasks for the server and the database watcher
    server = uvicorn.Server(uvicorn.Config(app, host=args.host, port=args.port))
    loop = asyncio.get_event_loop()
    loop.create_task(server.serve())
    loop.create_task(watch_database())

    try:
        await asyncio.gather(server.serve(), watch_database())
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
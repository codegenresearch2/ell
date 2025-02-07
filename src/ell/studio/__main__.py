import os
import uvicorn
from argparse import ArgumentParser
from ell.studio.data_server import create_app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
from watchfiles import awatch

# Database path
# Ensure the database path matches the gold code's format

def main():
    parser = ArgumentParser(description='ELL Studio Data Server')
    parser.add_argument('--storage-dir', default=os.getcwd(), help='Directory for filesystem serializer storage (default: current directory)')
    parser.add_argument('--host', default='127.0.0.1', help='Host to run the server on')
    parser.add_argument('--port', type=int, default=8080, help='Port to run the server on')
    parser.add_argument('--dev', action='store_true', help='Run in development mode')
    args = parser.parse_args()

    app = create_app(args.storage_dir)

    if not args.dev:
        # In production mode, serve the built React app
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        app.mount('/', StaticFiles(directory=static_dir, html=True), name='static')

        @app.get('/{full_path:path}')
        async def serve_react_app(full_path: str):
            return FileResponse(os.path.join(static_dir, 'index.html'))

    # Create a new event loop for managing the server and database watcher
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Define the database path
    db_path = os.path.join(args.storage_dir, 'ell.db')

    # Database watching function
    async def db_watcher():
        async for changes in awatch(db_path):
            print(f'Database changed: {changes}')

    # Run the server and the database watcher concurrently
    server_task = loop.create_task(uvicorn.Server(uvicorn.Config(app, host=args.host, port=args.port)).serve())
    db_watcher_task = loop.create_task(db_watcher())

    loop.run_until_complete(asyncio.gather(server_task, db_watcher_task))
    loop.close()
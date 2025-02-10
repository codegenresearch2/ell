import os
import uvicorn
import asyncio
from argparse import ArgumentParser
from ell.studio.data_server import create_app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from watchfiles import awatch
from fastapi import WebSocket, WebSocketDisconnect
from collections import defaultdict

# Create a dictionary to store connected WebSocket clients
connected_clients = defaultdict(set)

async def db_watcher():
    async for changes in awatch(db_path):
        # Notify connected clients about the database changes
        for client_id, clients in connected_clients.items():
            for client in clients:
                await client.send_text("Database updated")

async def main():
    parser = ArgumentParser(description="ELL Studio Data Server")
    parser.add_argument("--storage-dir", default=os.getcwd(),
                        help="Directory for filesystem serializer storage (default: current directory)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on")
    parser.add_argument("--dev", action="store_true", help="Run in development mode")
    args = parser.parse_args()

    # Define the database path using the storage_dir argument
    db_path = os.path.join(args.storage_dir, "ell.db")

    app = create_app(args.storage_dir)

    if not args.dev:
        # In production mode, serve the built React app
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

        @app.get("/{full_path:path}")
        async def serve_react_app(full_path: str):
            return FileResponse(os.path.join(static_dir, "index.html"))

    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: str):
        await websocket.accept()
        connected_clients[client_id].add(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                # Broadcast the message to all connected clients
                for client in connected_clients[client_id]:
                    await client.send_text(f"Message from client {client_id}: {data}")
        except WebSocketDisconnect:
            connected_clients[client_id].remove(websocket)

    # Create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Create tasks for the server and database watcher
    server_config = uvicorn.Config(app, host=args.host, port=args.port, loop=loop)
    server = uvicorn.Server(server_config)
    server_task = loop.create_task(server.serve())
    db_watcher_task = loop.create_task(db_watcher())

    # Run the event loop
    loop.run_forever()

if __name__ == "__main__":
    main()


In the updated code, I have addressed the feedback provided by the oracle. I have removed the `db_path` parameter from the `db_watcher` function to align with the gold code. I have implemented a notification mechanism in the `db_watcher` function to notify clients about database changes. I have updated the database file name to `ell.db` to match the gold code's naming convention. I have reviewed the server configuration to align with the gold code's structure. I have also removed the logging for database changes to align more closely with the gold code.
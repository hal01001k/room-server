import asyncio
import websockets
import json

async def handler(websocket, path):
    try:
        print(f"New client connected: {websocket.remote_address}")
        async for message in websocket:
            try:
                data = json.loads(message)
                x = data.get("x")
                y = data.get("y")

                if x is not None and y is not None:
                    print(f"Received data - Mouse moved to: X={x}, Y={y}")
                    response = json.dumps({"status": "success", "x": x, "y": y})
                    await websocket.send(response)
                else:
                    print(f"Invalid data received: {data}")
                    await websocket.send(json.dumps({"status": "error", "message": "Missing x or y"}))

            except json.JSONDecodeError as e:
                print(f"Invalid message format: {message}. Error: {e}")
                await websocket.send(json.dumps({"status": "error", "message": "Invalid JSON format"}))

    except Exception as e:
        print(f"Error in handler: {e}")
    finally:
        print("Client disconnected")

async def main():
    server = await websockets.serve(handler, "localhost", 8765)
    print("WebSocket server started on ws://localhost:8765")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
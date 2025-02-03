import asyncio
import websockets
import json

# Set to store all connected clients
connected_clients = set()

async def handler(websocket, path):
    try:
        # Add the new client to the set of connected clients
        connected_clients.add(websocket)
        print(f"New client connected: {websocket.remote_address}")
        print(f"Total connected clients: {len(connected_clients)}")

        async for message in websocket:
            try:
                # Parse the incoming message
                data = json.loads(message)
                x = data.get("x")
                y = data.get("y")

                if x is not None and y is not None:
                    print(f"Received data from {websocket.remote_address} - Mouse moved to: X={x}, Y={y}")
                    
                    # Prepare broadcast message
                    broadcast_message = json.dumps({
                        "status": "success", 
                        "x": x, 
                        "y": y,
                        "source": str(websocket.remote_address)  # Add source information
                    })
                    
                    # Broadcast to all connected clients except the sender
                    await broadcast(broadcast_message, websocket)

                else:
                    print(f"Invalid data received: {data}")
                    await websocket.send(json.dumps({"status": "error", "message": "Missing x or y"}))

            except json.JSONDecodeError as e:
                print(f"Invalid message format: {message}. Error: {e}")
                await websocket.send(json.dumps({"status": "error", "message": "Invalid JSON format"}))

    except Exception as e:
        print(f"Error in handler: {e}")
    finally:
        # Remove the client from the connected clients set
        connected_clients.remove(websocket)
        print(f"Client disconnected. Remaining clients: {len(connected_clients)}")

async def broadcast(message, sender):
    """
    Broadcast a message to all connected clients except the sender.
    
    :param message: JSON-encoded message to broadcast
    :param sender: WebSocket of the client that sent the original message
    """
    # Create a list of tasks to send the message to all clients except the sender
    tasks = [
        client.send(message) 
        for client in connected_clients 
        if client != sender
    ]
    
    # Run all send tasks concurrently
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

async def main():
    server = await websockets.serve(handler, "localhost", 8765)
    print("WebSocket server started on ws://localhost:8765")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
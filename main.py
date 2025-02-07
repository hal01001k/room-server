import json
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado.options import define, options

define("port", default=8765, help="run on the given port", type=int)

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    # Set to store all connected clients
    clients = set()
    
    def check_origin(self, origin):
        # Allow connections from any origin
        return True
        
    def open(self):
        # Add the new client to the set of connected clients
        WebSocketHandler.clients.add(self)
        print(f"New client connected: {self.request.remote_ip}")
        print(f"Total connected clients: {len(WebSocketHandler.clients)}")
        
    def on_message(self, message):
        try:
            # Parse the incoming message
            data = json.loads(message)
            x = data.get("x")
            y = data.get("y")
            
            if x is not None and y is not None:
                print(f"Received data from {self.request.remote_ip} - Mouse moved to: X={x}, Y={y}")
                
                # Prepare broadcast message
                broadcast_message = json.dumps({
                    "status": "success", 
                    "x": x, 
                    "y": y,
                    "source": self.request.remote_ip  # Add source information
                })
                
                # Broadcast to all connected clients except the sender
                self.broadcast(broadcast_message)
            else:
                print(f"Invalid data received: {data}")
                self.write_message(json.dumps({
                    "status": "error",
                    "message": "Missing x or y coordinates"
                }))
                
        except json.JSONDecodeError as e:
            print(f"Invalid message format: {message}. Error: {e}")
            self.write_message(json.dumps({
                "status": "error",
                "message": "Invalid JSON format"
            }))
        except Exception as e:
            print(f"Error processing message: {e}")
            self.write_message(json.dumps({
                "status": "error",
                "message": "Internal server error"
            }))
            
    def on_close(self):
        # Remove the client from the connected clients set
        WebSocketHandler.clients.remove(self)
        print(f"Client disconnected. Remaining clients: {len(WebSocketHandler.clients)}")
        
    def broadcast(self, message):
        """
        Broadcast a message to all connected clients except the sender.
        
        :param message: JSON-encoded message to broadcast
        """
        for client in WebSocketHandler.clients:
            if client != self:  # Don't send back to sender
                try:
                    client.write_message(message)
                except Exception as e:
                    print(f"Error broadcasting to client: {e}")

def make_app():
    return tornado.web.Application([
        (r"/", WebSocketHandler),
    ], debug=True)

def main():
    tornado.options.parse_command_line()
    app = make_app()
    app.listen(options.port)
    print(f"WebSocket server started on ws://localhost:{options.port}")
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()
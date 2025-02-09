import json
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado.options import define, options

define("port", default=8765, help="run on the given port", type=int)

# Initialize the array of size 275 with all values set to 0
state_array = [0] * 275

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    clients = set()
    
    def check_origin(self, _):
        return True
        
    def open(self):
        WebSocketHandler.clients.add(self)
        self.log_client_connection()
        
    def on_message(self, message):
        global state_array
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "boxclick":
                self.handle_boxclick(data)
            elif message_type == "mousemove":
                self.handle_mousemove(data)
            else:
                self.send_error_message("Unknown message type")
                
        except json.JSONDecodeError as e:
            self.send_error_message("Invalid JSON format")
        except Exception as e:
            self.send_error_message("Internal server error")
            
    def on_close(self):
        WebSocketHandler.clients.remove(self)
        self.log_client_disconnection()
        
    def broadcast(self, message):
        for client in WebSocketHandler.clients:
            if client != self:
                try:
                    client.write_message(message)
                except Exception as e:
                    print(f"Error broadcasting to client: {e}")
                    
    def handle_boxclick(self, data):
        global state_array
        index = data.get("index")
        additional_data = data.get("additionalData")
        
        if index is not None and additional_data is not None:
            if 0 <= index < len(state_array):
                state_array[index] = 1 - state_array[index]
                broadcast_message = json.dumps({
                    "status": "success", 
                    "type": "boxclick",
                    "index": index,
                    "additionalData": additional_data,
                    "source": self.request.remote_ip,
                    "newValue": state_array[index]
                })
                self.broadcast(broadcast_message)
            else:
                self.send_error_message("Index out of bounds")
        else:
            self.send_error_message("Missing index or additionalData")
            
    def handle_mousemove(self, data):
        x = data.get("x")
        y = data.get("y")
        additional_data = data.get("additionalData")
        
        if x is not None and y is not None and additional_data is not None:
            broadcast_message = json.dumps({
                "status": "success", 
                "type": "mousemove",
                "x": x, 
                "y": y,
                "additionalData": additional_data,
                "source": self.request.remote_ip
            })
            self.broadcast(broadcast_message)
        else:
            self.send_error_message("Missing x, y coordinates or additionalData")
            
    def send_error_message(self, message):
        self.write_message(json.dumps({
            "status": "error",
            "message": message
        }))
        
    def log_client_connection(self):
        print(f"New client connected: {self.request.remote_ip}")
        print(f"Total connected clients: {len(WebSocketHandler.clients)}")
        
    def log_client_disconnection(self):
        print(f"Client disconnected. Remaining clients: {len(WebSocketHandler.clients)}")

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

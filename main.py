import json
import logging
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado.options import define, options
from typing import Any, Dict

define("port", default=8765, help="run on the given port", type=int)

# Constants
STATE_ARRAY_SIZE = 275
DEFAULT_PORT = 8765
MESSAGE_TYPE_BOXCLICK = "boxclick"
MESSAGE_TYPE_MOUSEMOVE = "mousemove"

# Initialize the array of size 275 with all values set to 0
state_array = [0] * STATE_ARRAY_SIZE

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    clients = set()
    
    def check_origin(self, origin: str) -> bool:
        return True
        
    def open(self) -> None:
        WebSocketHandler.clients.add(self)
        self.log_client_connection()
        
    def on_message(self, message: str) -> None:
        global state_array
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == MESSAGE_TYPE_BOXCLICK:
                self.handle_boxclick(data)
            elif message_type == MESSAGE_TYPE_MOUSEMOVE:
                self.handle_mousemove(data)
            else:
                self.send_error_message("Unknown message type")
                
        except json.JSONDecodeError:
            self.send_error_message("Invalid JSON format")
        except Exception:
            self.send_error_message("Internal server error")
            
    def on_close(self) -> None:
        WebSocketHandler.clients.remove(self)
        self.log_client_disconnection()
        
    def broadcast(self, message: str) -> None:
        for client in WebSocketHandler.clients:
            if client != self:
                try:
                    client.write_message(message)
                except Exception as e:
                    logging.error(f"Error broadcasting to client: {e}")
                    
    def handle_boxclick(self, data: Dict[str, Any]) -> None:
        global state_array
        index = data.get("index")
        additional_data = data.get("additionalData")
        
        if index is not None and additional_data is not None:
            if 0 <= index < len(state_array):
                state_array[index] = 1 - state_array[index]
                broadcast_message = self.create_broadcast_message(
                    MESSAGE_TYPE_BOXCLICK, index=index, additional_data=additional_data, new_value=state_array[index]
                )
                self.broadcast(broadcast_message)
            else:
                self.send_error_message("Index out of bounds")
        else:
            self.send_error_message("Missing index or additionalData")
            
    def handle_mousemove(self, data: Dict[str, Any]) -> None:
        x = data.get("x")
        y = data.get("y")
        additional_data = data.get("additionalData")
        
        if x is not None and y is not None and additional_data is not None:
            broadcast_message = self.create_broadcast_message(
                MESSAGE_TYPE_MOUSEMOVE, x=x, y=y, additional_data=additional_data
            )
            self.broadcast(broadcast_message)
        else:
            self.send_error_message("Missing x, y coordinates or additionalData")
            
    def send_error_message(self, message: str) -> None:
        self.write_message(json.dumps({
            "status": "error",
            "message": message
        }))
        
    def log_client_connection(self) -> None:
        logging.info(f"New client connected: {self.request.remote_ip}")
        logging.info(f"Total connected clients: {len(WebSocketHandler.clients)}")
        
    def log_client_disconnection(self) -> None:
        logging.info(f"Client disconnected. Remaining clients: {len(WebSocketHandler.clients)}")
        
    def create_broadcast_message(self, message_type: str, **kwargs: Any) -> str:
        message = {
            "status": "success",
            "type": message_type,
            "source": self.request.remote_ip
        }
        message.update(kwargs)
        return json.dumps(message)

def make_app() -> tornado.web.Application:
    return tornado.web.Application([
        (r"/", WebSocketHandler),
    ], debug=True)

def main() -> None:
    tornado.options.parse_command_line()
    app = make_app()
    app.listen(options.port)
    logging.info(f"WebSocket server started on ws://localhost:{options.port}")
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

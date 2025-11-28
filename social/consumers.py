import json
from channels.generic.websocket import WebsocketConsumer

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        # Accept the WebSocket connection
        self.accept()
        self.send(text_data=json.dumps({"message": "WebSocket connection established"}))

    def disconnect(self, close_code):
        # Handle WebSocket disconnection
        pass

    def receive(self, text_data):
        # Handle messages received from the WebSocket
        data = json.loads(text_data)
        message = data.get("message", "No message received")
        
        # Echo the message back to the client
        self.send(text_data=json.dumps({"message": message}))
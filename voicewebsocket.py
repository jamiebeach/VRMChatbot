from flask_socketio import SocketIO, emit
from flask import request
from websocket import create_connection, WebSocket
import threading
import time

def start_proxy(ws_url, sid, socketio):
    """
    Handles the proxying of WebSocket messages between the client and the target server.
    Each client connection will have its own dedicated WebSocket connection to the target.
    """
    print('creating websocket for ' + ws_url)
    ws = None
    try:
        ws = create_connection(ws_url)
    except:
        print("ERROR: UNABLE TO CREATE VOICE WEB SOCKET")

    def send_to_client():
        """Receives messages from the target WebSocket server and forwards them to the client."""
        if(ws == None):
            print("ERROR: ws is None")
            return
        
        try:
            while True:
                message = ws.recv()
                print('voicewebsocket: send_to_client, message recv : ');

                if(len(message) < 10000):
                    print(message[:50])
                
                print('sending the message')
                socketio.emit('voice_message', {'data': message}, to=sid)
                print('message sent')
        except Exception as e:
            print(f"Error receiving message from target WebSocket: {e}")
        finally:
            ws.close()

    def send_to_server(message):
        """Sends a client's message to the target WebSocket server."""
        if(ws == None):
            print("ERROR: ws is None")
            return
        
        print('send to server')
        try:
            print('sending message')
            ws.send(message)
            print('message sent')
        except Exception as e:
            print(f"Error sending message to target WebSocket: {e}")


    receiver_thread = threading.Thread(target=send_to_client)
    receiver_thread.start()
    return send_to_server
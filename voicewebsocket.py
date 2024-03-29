from flask_socketio import SocketIO, emit
from flask import request
from websocket import create_connection, WebSocket
import threading


def start_proxy(ws_url, sid, socketio):
    """
    Handles the proxying of WebSocket messages between the client and the target server.
    Each client connection will have its own dedicated WebSocket connection to the target.
    """
    print('creating websocket for ' + ws_url)
    ws = create_connection(ws_url)

    def send_to_client():
        """Receives messages from the target WebSocket server and forwards them to the client."""
        try:
            while True:
                message = ws.recv()
                print('voicewebsocket: send_to_client, message recv : ');

                if(len(message) < 10000):
                    print(message)
                
                print('sending the message')
                socketio.emit('message', {'data': message}, to=sid)
                print('message sent')
        except Exception as e:
            print(f"Error receiving message from target WebSocket: {e}")
        finally:
            ws.close()

    def send_to_server(message):
        """Sends a client's message to the target WebSocket server."""
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
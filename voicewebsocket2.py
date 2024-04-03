from flask_socketio import SocketIO, emit
from flask import request
from websocket import create_connection, WebSocketException
import threading
import time

def attempt_reconnect(ws_url, retry_interval=5, sid=None, socketio=None):
    """
    Attempts to reconnect to the WebSocket server every 'retry_interval' seconds.
    Once connected, it starts the proxying process.
    
    Args:
        ws_url (str): WebSocket URL of the target server.
        retry_interval (int): Time in seconds between reconnection attempts.
        sid (str): Session ID for the client.
        socketio (SocketIO): Flask-SocketIO instance for communication with the client.
    """
    counter = 0
    while True:
        counter = counter + 1
        if(counter > 5):
            print('tried 5 times. Breaking from connectivity attempts to tts server')
            break

        try:
            print("("+ str(sid) + ") Attempting to connect to tts server websocket - " + ws_url)
            ws = create_connection(ws_url)
            print("("+ str(sid) + ") Connected to the tts WebSocket server.")
            if sid and socketio:
                start_proxying(ws, sid, socketio)
            break
        except WebSocketException as e:
            print(f"({str(sid)}) Failed to connect to {ws_url}. Retrying in {retry_interval} seconds...")
            time.sleep(retry_interval)
        except Exception as e:
            print(f"({str(sid)}) An unexpected error occurred: {e}")
            time.sleep(retry_interval)

def start_proxying(ws, sid, socketio):
    """
    Starts the proxying of WebSocket messages once a connection is established.
    """
    def send_to_client():
        """Receives messages from the target WebSocket server and forwards them to the client."""
        try:
            while True:
                message = ws.recv()
                if len(message) < 10000:
                    print(f"({str(sid)}) Message received: {message[:50]}...")
                socketio.emit('message', {'data': message}, to=sid)
        except Exception as e:
            print(f"({str(sid)}) Error receiving message from target WebSocket: {e}")
        finally:
            ws.close()

    def send_to_server(message):
        """Sends a client's message to the target WebSocket server."""
        try:
            ws.send(message)
        except Exception as e:
            print(f"({str(sid)}) Error sending message to target WebSocket: {e}")

    receiver_thread = threading.Thread(target=send_to_client)
    receiver_thread.start()
    return send_to_server

def start_proxy(ws_url, sid, socketio):
    """
    Initiates the connection to the WebSocket server and handles proxying between
    the client and the server. Manages reconnection attempts if the initial connection fails.
    """
    print(f'({str(sid)}) Attempting to create a WebSocket connection to ' + ws_url)
    try:
        ws = create_connection(ws_url)
        print(f"({str(sid)}) Connection established with the tts server.")
        return start_proxying(ws, sid, socketio)
    except WebSocketException:
        print(f"({str(sid)}) Initial connection failed connecting to tts server. Attempting to reconnect in the background...")
        # Start a new thread to attempt reconnection
        reconnection_thread = threading.Thread(target=attempt_reconnect, args=(ws_url, 5, sid, socketio))
        reconnection_thread.daemon = True
        reconnection_thread.start()
    except Exception as e:
        print(f"({str(sid)}) An unexpected error occurred connecting to tts server while trying to connect: {e}")
        reconnection_thread = threading.Thread(target=attempt_reconnect, args=(ws_url, 5, sid, socketio))
        reconnection_thread.daemon = True
        reconnection_thread.start()

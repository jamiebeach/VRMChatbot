from flask import request
from shared_resources import client_sessions
from chatbot.chatbot import Chatbot
import xml.etree.ElementTree as ET
import json
import voicewebsocket as voicewebsocket

class VoiceController:
    def __init__(self, socketio, config):
        self.socketio = socketio
        self.config = config
        self.target_ws_url = config['TTS_SERVER_URL']
        self.client_sessions = {}

        @socketio.on('disconnect')
        def handle_disconnect():
            print('Client disconnected:', request.sid)
            # Remove the session from the dictionary to clean up
            if request.sid in self.client_sessions:
                del self.client_sessions[request.sid]

        @socketio.on('voice_message')
        def handle_message(message):
            print('Message from client:', message)
            sid = request.sid
            if sid in client_sessions:
                # Retrieve the send_to_server function for this client and use it to forward the message
                send_to_server = self.client_sessions[sid]
                send_to_server(message)  # Assuming the message is a dictionary with a 'data' key

    def addClient(self, sid):
        send_to_server = voicewebsocket.start_proxy(self.target_ws_url, sid, self.socketio)
        self.client_sessions[sid] = send_to_server
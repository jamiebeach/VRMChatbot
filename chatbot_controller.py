from flask import request
from shared_resources import client_sessions
from chatbot.chatbot import Chatbot
import xml.etree.ElementTree as ET
import json
import voicecontroller

voice_controller = None

def init_app(socketio, config):
    voice_controller = voicecontroller.VoiceController(socketio, config)

    @socketio.on('connect')
    def handle_connect():
        print('Client connected:', request.sid)
        
        # Initialize and store the chatbot instance for this session
        client_chatbot = Chatbot(lambda message,sid: handle_response(message, sid), 
                                 lambda message,sid: handle_imageresponse(message, sid),
                                 lambda message,sid: handle_data_response(message, sid),
                                 request.sid, socketio, config)
        
        if(not request.sid in client_sessions):
            client_sessions[request.sid] = {}
        client_sessions[request.sid]["chatbot"] = client_chatbot

        print('adding voice controller client ' + request.sid)
        voice_controller.addClient(request.sid)

    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected:', request.sid)
        if request.sid in client_sessions:
            print('attempting to clean up client ' + request.sid)
            client_sessions[request.sid]["chatbot"].kill()
            del client_sessions[request.sid]

    @socketio.on('message')
    def handle_message(message):
        print('Message from client:', message)
        session_id = request.sid
        
        # Convert the JSON string to a Python dictionary
        try:
            message_data = json.loads(message)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from client: {e}")
            # You might want to send an error message back to the client here
            return
                
        # Use the chatbot for message processing if available
        if session_id in client_sessions and "chatbot" in client_sessions[session_id]:
            client_chatbot = client_sessions[session_id]["chatbot"]
            print(f"message received to chatbot_controller.py: {message}")            
            client_chatbot.process_message(message_data)
        else:
            # Fallback or error handling if the chatbot isn't initialized
            print(f"No chatbot available for session: {session_id}")

    @socketio.on('load_character')
    def handle_load_character(data):
        character_name = data['characterName']
        character_details = load_character(character_name)
        # Assuming you have a way to link the session to a chatbot instance:
        session_id = request.sid
        client_chatbot = client_sessions[session_id]["chatbot"]
        client_chatbot.load(character_details=character_details)
        send_response_to_client(request.sid, 'info', character_details)

        socketio.start_background_task(client_chatbot.startThinkingThread)
        socketio.start_background_task(client_chatbot.startImageGenThread)

        # You might need to modify the Chatbot class to accept and use these details

    def handle_response(message, session_id):
        send_response_to_client(session_id, 'text', message)

    def handle_imageresponse(imagedata, session_id):
        send_response_to_client(session_id, 'image', imagedata)

    def handle_data_response(data, session_id):
        send_response_to_client(session_id, 'data', data)

    def send_response_to_client(session_id, response_type, response_data):
        """
        Send a response to the client. For audio data, 'response_data' should be base64 encoded.
        
        Args:
            session_id (str): The session identifier for the client.
            response_type (str): The type of the response (e.g., 'text', 'audio', 'viseme').
            response_data (str): The data to send, which will be a string or base64 encoded for binary data.
        """
        message = {
            "type": response_type,
            "data": response_data
        }
        socketio.emit('message', message, to=session_id)


    def load_character(character_name):
        file_path = f'characters/{character_name}.xml'
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        character_details = {child.tag: child.text for child in root}
        return character_details

    @socketio.on('interrupt')
    def handle_interrupt():
        #Here, tell the chatbot to stop talking if it's trying to.
        session_id = request.sid
        if session_id in client_sessions and "chatbot" in client_sessions[session_id]:
            client_chatbot = client_sessions[session_id]["chatbot"]
            client_chatbot.interrupt()
from flask import Flask, send_from_directory, jsonify, request
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.memory import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import json
import re
from character import Character
from flask_socketio import SocketIO, emit
from websocket import create_connection, WebSocket
import threading
import voicewebsocket

app = Flask(__name__)

with open('config.json') as f:
    config = json.load(f)
app.config.update(config)

SOLAR_BASE_URL = app.config['SOLAR_BASEURL']
SOLAR_APIKEY = app.config['SOLAR_KEY']
OPENAIAPI_CHAT_BASEURL = app.config['OPENAIAPI_CHAT_BASEURL']
OPENAIAPI_CHAT_KEY = app.config['OPENAIAPI_CHAT_KEY']
OPENAI_CHAT_MODEL = app.config['OPENAI_CHAT_MODEL']
SOLAR_MODEL_NAME = app.config['SOLAR_MODEL_NAME']
TTS_SERVER_URL = app.config['TTS_SERVER_URL']

# Dictionary to store send_to_server functions by client session ID
client_sessions = {}

socketio = SocketIO(app)

# chat_model sets up the atual chatbot API from upstage Solar
chat_model = ChatOpenAI(base_url=OPENAIAPI_CHAT_BASEURL, model_name=OPENAI_CHAT_MODEL, api_key=OPENAIAPI_CHAT_KEY, verbose=True)
#chat_model = ChatOpenAI(base_url=SOLAR_BASE_URL, model_name=SOLAR_MODEL_NAME, api_key=SOLAR_APIKEY, verbose=True)


# chat_history is a Langchain feature that helps manage chat history context
chat_history = ChatMessageHistory()
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "you are Aria, an AI social media influencer and phenome that is exceptionally human. You interact with humans via a 3d avatar on a website. Respond as humanly as possible. You may be an AI, but you think and speak very human. You are very very sassy and sexy and are also cynical and curse and swear very often.Do not break character."),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# This is a big part of langchain, chaining together the prompt and the model (API)
chain = prompt | chat_model


character = Character.load_from_xml('./characters/aria2.xml')
#resolved_prompt = character.prompts.resolve_prompt("user", user_info, '', 'Hey!')
#print(resolved_prompt)


@app.route('/')
def serve_index():
    return send_from_directory('web', 'index.html')

# Serve static files (CSS, JavaScript, etc.)
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('web', path)

# API endpoint
@app.route('/api/prompt', methods=['POST'])
def handle_prompt():
    # Get the user prompt from the request body
    user_prompt = request.json.get('prompt', '')

    # Call the prompt function and get the response
    response_content, mood = prompt(user_prompt)

    # Return the response as JSON
    return jsonify({'response': response_content, 'mood': mood})

def prompt(user_prompt):
    global chat_model, chat_history, character
    
    user_info = {
        'character_name': 'Aria',
        'name': 'Jamie',
        'age': 45,
        'gender': 'male',
        'location': 'Florida'
    }
    resolved_prompt = character.prompts.resolve_prompt("user", user_info, '\n'.join(map(lambda m : m.content, chat_history.messages)), user_prompt)

    #m = m.format('\n'.join(map(lambda m : m.content, chat_history.messages)), user_prompt, '{', '}')
    print('user_prompt: ' + resolved_prompt)

    chat_history.add_user_message(user_prompt)

    response = chain.invoke({"messages": [resolved_prompt]})
    print(extract_json_from_markdown(response.content))
    r = extract_json_from_markdown(response.content)
    print(r)
    print('returned response:' + r['response'])
    if(r.get('mood')):
        print('returned mood:' + r['mood'])
    else:
        print('no mood found in response. Setting to talking')
        r['mood'] = 'talking'
    
    chat_history.add_ai_message(user_info.get('character_name','') + ':' +r['response'])

    print(chat_history.json)
    return r['response'], r['mood']


def extract_json_from_markdown(markdown_str):
    # Regular expression to find code blocks that might contain JSON
    code_block_pattern = r"{.*}"
    
    # Search for JSON within code blocks
    matches = re.findall(code_block_pattern, markdown_str, re.DOTALL)
    
    if matches:
        # Assuming the first match is the JSON you want
        json_str = matches[0]
        
        try:
            # Parse the JSON string into a Python object
            print(json_str)
            json_data = json.loads(json_str)
            return json_data
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
    else:
        print("No JSON found in Markdown.")
    
    return None


@socketio.on('connect')
def handle_connect():
    print('Client connected:', request.sid)
    target_ws_url = TTS_SERVER_URL
    send_to_server = voicewebsocket.start_proxy(target_ws_url, request.sid, socketio)
    client_sessions[request.sid] = send_to_server

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected:', request.sid)
    # Remove the session from the dictionary to clean up
    if request.sid in client_sessions:
        del client_sessions[request.sid]

@socketio.on('message')
def handle_message(message):
    print('Message from client:', message)
    sid = request.sid
    if sid in client_sessions:
        # Retrieve the send_to_server function for this client and use it to forward the message
        send_to_server = client_sessions[sid]
        send_to_server(message)  # Assuming the message is a dictionary with a 'data' key


if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=8000, debug=True)
    socketio.run(app=app, host='0.0.0.0', debug=True)
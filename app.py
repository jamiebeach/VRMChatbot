from flask import Flask, send_from_directory, jsonify, request, session
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
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key'

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
THINK_FREQUENCY_SECONDS = app.config['THINK_FREQUENCY_SECONDS']
DEFAULT_CHARACTER = app.config['DEFAULT_CHARACTER']
CHARACTER_PATH = app.config['CHARACTER_PATH']

# Dictionary to store send_to_server functions by client session ID
client_sessions = {}

socketio = SocketIO(app)

# chat_model sets up the atual chatbot API from upstage Solar
chat_model = ChatOpenAI(base_url=OPENAIAPI_CHAT_BASEURL, model_name=OPENAI_CHAT_MODEL, api_key=OPENAIAPI_CHAT_KEY, verbose=True)
#chat_model = ChatOpenAI(base_url=SOLAR_BASE_URL, model_name=SOLAR_MODEL_NAME, api_key=SOLAR_APIKEY, verbose=True)
  
character = Character.load_from_xml(DEFAULT_CHARACTER)

# chat_history is a Langchain feature that helps manage chat history context
chat_history = ChatMessageHistory()

summarizations = {}

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

@app.route('/')
def serve_index():
    # Ensure there's a session ID
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

    # Now you can access session['session_id'] as the session ID
    session_id = session['session_id']

    return send_from_directory('web', 'index.html')

# Serve static files (CSS, JavaScript, etc.)
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('web', path)

@app.route('/api/restart', methods=['GET'])
def handle_restart():
    print('in handle_restart')
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

    # Now you can access session['session_id'] as the session ID
    session_id = session['session_id']

    chat_history.clear()
    summarizations[session_id] = []
    return jsonify({'cleared'})
    
# API endpoint
@app.route('/api/prompt', methods=['POST'])
def handle_prompt():
    # Ensure there's a session ID
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

    # Now you can access session['session_id'] as the session ID
    session_id = session['session_id']

    # Get the user prompt from the request body
    user_prompt = request.json.get('prompt', '')
    
    # Call the prompt function and get the response
    response_content, mood = prompt(user_prompt, session_id)

    # Return the response as JSON
    return jsonify({'response': response_content, 'mood': mood})

###############################################
# Prompt
###############################################
def prompt(user_prompt, sid, botstate="response"):
    global chat_model, chat_history, character
    
    user_info = {
        'name': 'Jamie',
        'age': 45,
        'gender': 'male',
        'location': 'Florida'
    }

    stringChatHistory = '\n'.join(map(lambda m : m.content, chat_history.messages))

    if(len(stringChatHistory) > 5200):
        # Let's summarize the chat history to avoid context overflow
        print('Chat history is beyond 1200 characters. Summarizing...')
        summary = chain.invoke({"messages":['The following is a chat transcript between ' + user_info.get('name') + ' (human) and ' + character.name + ' (an AI). Please summarize this as succinctly as possible, avoid large words and make sure to describe both characters\' thoughts : ' + stringChatHistory]})
        summary = summary.content.strip().replace('\n', '')
        print('Chat history summary is : ' + summary)

        if(summarizations.get(sid) == None):
            print('summarization does not yet exist for session. Creating new')
            summarizations[sid] = []
        print('appending summarization')
        summarizations[sid].append(summary)
        print('new full chat summary:\n--------------------\n' + '\n'.join(summarizations))
        print('-----------------------------')
        chat_history.clear()

    stringChatSummary = ''
    if(summarizations.get('sid')):
        stringChatSummary = '\n'.join(summarizations)

    resolved_prompt = character.prompts.resolve_prompt("user", 
                                                       user_info, 
                                                       character.getinfo(), 
                                                       stringChatHistory,
                                                       stringChatSummary, 
                                                       user_prompt, 
                                                       "response")

    print('user_prompt: ' + resolved_prompt)

    chat_history.add_user_message(user_info.get('name','') + ':' + user_prompt)

    response = chain.invoke({"messages": [resolved_prompt]})

    extractedJSONResponse = extract_json_from_markdown(response.content)
    counter = 0
    while(extractedJSONResponse == None and counter < 3):
        response = chain.invoke({"messages": [resolved_prompt]})
        extractedJSONResponse = extract_json_from_markdown(response.content) 
        counter = counter + 1

    if(extractedJSONResponse == None):
        extractedJSONResponse = {"response":"Error", "mood":"sad"}

    print('extracted JSON:' + str(extractedJSONResponse))
        
    if(extractedJSONResponse.get('mood')):
        print('returned mood:' + extractedJSONResponse['mood'])
    else:
        print('no mood found in response. Setting to talking')
        extractedJSONResponse['mood'] = 'talking'
    
    chat_history.add_ai_message(character.name + ':' +extractedJSONResponse['response'])

    print(chat_history.json)
    return extractedJSONResponse['response'], extractedJSONResponse['mood']


def extract_json_from_markdown(markdown_str, counter = 0):
    # Regular expression to find code blocks that might contain JSON
    code_block_pattern = r"{.*}"
    
    print('in extract_json')
    print(markdown_str)
    markdown_str = str(markdown_str).replace("\n", "")

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

            if(counter >= 1):
                print('not working after attempt to fix. Return none')
                return None
            else :
                # Let's call the chatbot again to fix the JSON
                print('JSON Was invalid... Asking llm to fix it')
                response = chain.invoke({"messages": ['Please respond with a valid and fixed version of the following JSON: ' + json_str]})
                return extract_json_from_markdown(response.content, counter + 1)
    else:
        print("No JSON found in Markdown.")
    
    return None
    return json.loads('{"response":"sorry... I errored out.", "mood":"sad"}')


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
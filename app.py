from flask import Flask, send_from_directory, jsonify, request
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.memory import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import json

app = Flask(__name__)

with open('config.json') as f:
    config = json.load('config.json')
app.config.update(config)

BASE_URL = app.config['SOLAR_BASEURL']
APIKEY = app.config['SOLAR_KEY']

# chat_model sets up the atual chatbot API from upstage Solar
chat_model = ChatOpenAI(base_url=BASE_URL, model_name="solar-1-mini-chat", api_key=APIKEY)

# chat_history is a Langchain feature that helps manage chat history context
chat_history = ChatMessageHistory()
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant. Answer all questions to the best of your ability.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# This is a big part of langchain, chaining together the prompt and the model (API)
chain = prompt | chat_model

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
    response_content = prompt(user_prompt)

    # Return the response as JSON
    return jsonify({'response': response_content})

def prompt(user_prompt):
    global chat_model, chat_history

    chat_history.add_user_message(("(act as human friend to user. "
                                   "Don't act like an ai. "
                                   "Don't act like an assistant. " 
                                   "Do not break character) user prompt: ") + user_prompt)

    response = chain.invoke({"messages": chat_history.messages})

    chat_history.add_ai_message(response)
    return response.content

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
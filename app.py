from flask import Flask, send_from_directory, jsonify, request, session, render_template
from flask_socketio import SocketIO
from chatbot_controller import init_app as init_chatbot_controller
from config import DevelopmentConfig
import uuid

app = Flask(__name__)
app.config.from_object(DevelopmentConfig())
socketio = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=False)

init_chatbot_controller(socketio, app.config)

@app.route('/tester')
def home():
    return render_template('tester.html')

@app.route('/')
def serve_index():
    return send_from_directory('web', 'index.html')

# Serve static files (CSS, JavaScript, etc.)
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('web', path)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=app.config['DEBUG'])

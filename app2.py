from flask import Flask, render_template
from flask_socketio import SocketIO
from chatbot_controller import init_app as init_chatbot_controller
from config import DevelopmentConfig

app = Flask(__name__)
app.config.from_object(DevelopmentConfig())
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

init_chatbot_controller(socketio, app.config)

@app.route('/tester')
def home():
    return render_template('tester.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=app.config['DEBUG'])

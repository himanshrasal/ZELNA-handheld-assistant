from flask import Flask
from flask_socketio import SocketIO

testdata = [
    {"message": "Can you help me with the project?", "sender": "server"},
    {"message": "Sure! What do you need help with?", "sender": "client"},
    {"message": "You're welcome! Let me know if you need anything else.", "sender": "server"},
    {"message": "Thank you, that's very helpful.", "sender": "client"},
    {"message": "I'm doing well, thanks for asking.", "sender": "server"},
    {"message": "Hello, how are you?", "sender": "client"},
    {"message": "Thank you, that's very helpful.", "sender": "server"},
    {"message": "Can you help me with the project?", "sender": "client"},
    {"message": "You're welcome! Let me know if you need anything else.", "sender": "server"},
    {"message": "I'm doing well, thanks for asking.", "sender": "client"}
]


socketio = SocketIO()

@socketio.on('connect')
def handleConnection(auth):
    print("client connected!", str(auth))
    socketio.emit('initialize', testdata)
    print("testdata sent")
    
@socketio.on('initializeAck')
def handleHelo(data):
    print(data)
    

def sendInitialData():
    socketio.emit('initialize', testdata)
    


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    socketio.init_app(app)
    return app

if __name__ == '__main__':
    app = create_app()
    socketio.run(app)
    
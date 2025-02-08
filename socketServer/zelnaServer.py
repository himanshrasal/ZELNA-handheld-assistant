from flask import Flask, render_template
from flask_socketio import SocketIO

socketio = SocketIO()

@socketio.on('connect')
def handleConnection(auth):
    print("client connected!", str(auth))

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    socketio.init_app(app)
    return app

if __name__ == '__main__':
    app = create_app()
    socketio.run(app)
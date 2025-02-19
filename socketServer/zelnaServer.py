from flask import Flask
from flask_socketio import SocketIO

testdata = [
    {"message": "1", "sender": "server"},
    {"message": "2", "sender": "client"},
    {"message": "3", "sender": "server"},
    {"message": "4", "sender": "client"},
    {"message": "5", "sender": "server"},
    {"message": "6", "sender": "client"},
    {"message": "7", "sender": "server"},
    {"message": "Can you help me with the project?", "sender": "client"},
    {
        "message": "You're welcome! Let me know if you need anything else.",
        "sender": "server",
    },
    {"message": "I'm doing well, thanks for asking.", "sender": "client"},
]


socketio = SocketIO()


@socketio.on("connect")
def handleConnection(auth):
    print("client connected!", str(auth))
    socketio.emit("initialize", testdata)
    print("testdata sent")


@socketio.on("disconnect")
def handleDisconnection():
    print("client disconnected")
    
@socketio.on("message")
def handleMessage(data):
    socketio.emit("response", {"message": "message recived", "sender": "server"})
    print("message received", data)


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "secret!"
    socketio.init_app(app)
    return app


if __name__ == "__main__":
    app = create_app()
    socketio.run(app, host="0.0.0.0", port=5000)

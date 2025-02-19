import json
from flask import Flask
from flask_socketio import SocketIO
import ollama

socketio = SocketIO()
messages = []

try:

    @socketio.on("connect")
    def handleConnection(auth):
        global messages
        loaded_messages = load_messages_from_file()
        
        existing_messages = set(json.dumps(m) for m in messages)  # Serialize for hashability
        new_messages = [m for m in loaded_messages if json.dumps(m) not in existing_messages]
        messages.extend(new_messages)  # Efficiently append unique messages

        print("Client connected!", str(auth))
        socketio.emit("initialize", parseOllamaMessageArrayToJson(messages))
        print("Chat history sent to client")

    @socketio.on("disconnect")
    def handleDisconnection():
        global messages
        print("client disconnected. Saving messages")
        save_messages_to_file(messages)

    @socketio.on("message")
    def handleMessage(message):
        global messages
        if message.lower().replace(" ", "") == "clearmessages":
            save_messages_to_file([])
            messages = []
            print("messages cleared")
            socketio.emit("initialize", [])
            return
        
        print("message received", message)
        response = chatWithHistory(message)
        socketio.emit("response", {"message": response, "sender": "server"})
        print(f"response sent: {response}")

except Exception as e:
    print(f"socketio exception {e}")


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "secret!"
    socketio.init_app(app)
    return app


def chatWithHistory(input):
    global messages
    model = "llama3.2:1b"
    maxHistory = 20

    while True:
        if len(messages) > maxHistory * 2:
            messages = messages[-(maxHistory * 2) :]

        messages.append({"role": "user", "content": input})

        try:
            response = ollama.chat(model=model, messages=messages)
            responseContent = response["message"]["content"]
            messages.append({"role": "assistant", "content": responseContent})

            print(responseContent)
            return responseContent

        except Exception as e:
            print(f"error while running ollama chat {e}")
            return "Response could not be generated :( "


def parseOllamaMessageArrayToJson(messages):
    data = []
    for message in messages:
        if message.get("role") == "assistant":
            data.append({"sender": "server", "message": message.get("content")})
        if message.get("role") == "user":
            data.append({"sender": "client", "message": message.get("content")})

    return data


def save_messages_to_file(messages, filename="chat_history.json"):
    with open(filename, "w") as file:
        json.dump(messages, file, indent=2)
    print(f"Messages saved to {filename}")


def load_messages_from_file(filename="chat_history.json"):
    try:
        with open(filename, "r") as file:
            fileMessages = json.load(file)
        print(f"Messages loaded from {filename}")
        return fileMessages
    except FileNotFoundError:
        print(f"No existing file found. Starting fresh.")
        return []


if __name__ == "__main__":
    app = create_app()
    socketio.run(app, host="0.0.0.0", port=5000)

import json, ollama, re, pyttsx3, base64
from flask import Flask
from flask_socketio import SocketIO

# Initialize SocketIO and global message storage
socketio = SocketIO()
messages = []
    
#initialize pyttsx3 voice engine
engine = pyttsx3.init()
engine.setProperty("rate", 180)
engine.setProperty("volume", 1.0)
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[2].id)

def create_app():
    """Create and configure Flask app with SocketIO."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "secret!"
    socketio.init_app(app, cors_allowed_origins="*")
    return app

def clean_text(text):
    """Remove markdown-like formatting symbols from the text."""
    return re.sub(r'[\*_/`~|<>]', '', text)

def chatWithHistory(input):
    """Handle chat input while maintaining message history."""
    global messages
    model = "llama3.1:8b"
    maxHistory = 20

    # Trim message history to avoid overflow
    if len(messages) > maxHistory * 2:
        messages = messages[-(maxHistory * 2) :]

    messages.append({"role": "user", "content": input})

    try:
        response = ollama.chat(model=model, messages=messages)
        responseContent = clean_text(response["message"]["content"])
        messages.append({"role": "assistant", "content": responseContent})
        # print(responseContent)
        return responseContent

    except Exception as e:
        print(f"Error while running ollama chat: {e}")
        return "Response could not be generated :("


def parseOllamaMessageArrayToJson(messages):
    """Convert message history into JSON format for the client."""
    return [
        {"sender": "server" if m.get("role") == "assistant" else "client", "message": m.get("content")}
        for m in messages
    ]


def save_messages_to_file(messages, filename="chat_history.json"):
    """Save message history to a file."""
    with open(filename, "w") as file:
        json.dump(messages, file, indent=2)
    print(f"Messages saved to {filename}")


def load_messages_from_file(filename="chat_history.json"):
    """Load message history from a file."""
    try:
        with open(filename, "r") as file:
            fileMessages = json.load(file)
        print(f"Messages loaded from {filename}")
        return fileMessages
    except FileNotFoundError:
        print("No existing file found. Starting fresh.")
        return []
    
def TTS(text:str, path:str = "output.mp3"):
    """Text to speech function using pyttsx3 engine"""
    try:
        engine.save_to_file(text, path)
        engine.runAndWait()
        engine.stop()
        return True
    except Exception as e:
        print(f"Error while running TTS: {e}")
        return False

@socketio.on("connect")
def handleConnection(auth):
    """Handle client connections."""
    global messages
    try:
        loaded_messages = load_messages_from_file()
        # Add only unique messages
        existing_messages = set(json.dumps(m) for m in messages)
        new_messages = [m for m in loaded_messages if json.dumps(m) not in existing_messages]
        messages.extend(new_messages)

        print("Client connected!", str(auth))
        socketio.emit("initialize", parseOllamaMessageArrayToJson(messages))
        print("Chat history sent to client")

    except Exception as e:
        print(f"Error during client connection: {e}")
        socketio.emit("error", {"message": "Failed to initialize chat history"})


@socketio.on("disconnect")
def handleDisconnection():
    """Handle client disconnections."""
    global messages
    print("Client disconnected. Saving messages.")
    save_messages_to_file(messages)


@socketio.on("message")
def handleMessage(message):
    """Process incoming messages from the client."""
    global messages
    try:
        # Support "clearmessages" command
        if message.lower().replace(" ", "") == "clearmessages":
            save_messages_to_file([])
            messages = []
            print("Messages cleared")
            socketio.emit("initialize", [])
            return

        print(f"Message received: {message}")

        # Process message from ollama and send response
        response = chatWithHistory(message)
        socketio.emit("response", {"message": response, "sender": "server"})
        save_messages_to_file(messages)
        print(f"Response sent: {response}")

        # Convert response to speech
        if TTS(response, "output.mp3"):
            with open("output.mp3", "rb") as file:
                encoded = base64.b64encode(file.read()).decode("utf-8")

            socketio.emit("tts_audio", {"file": encoded})
        
        else:
            socketio.emit("response", {"message": "Failed to generate TTS", "sender": "info"})
                
    except Exception as e:
        print(f"Error while handling message: {e}")
        socketio.emit("response", {"message": "Failed to process message", "sender": "server"})


if __name__ == "__main__":
    try:
        app = create_app()
        socketio.run(app, host="0.0.0.0", port=5000, debug=True)
    except Exception as e:
        print(f"SocketIO server failed to start: {e}")
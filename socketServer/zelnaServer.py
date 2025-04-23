import json, ollama, re, pyttsx3, base64, subprocess, os
from flask import Flask
from flask_socketio import SocketIO

# Initialize SocketIO and global message storage
socketio = SocketIO()
messages = []

LANGUAGE_MODEL = "llama3.1:8b"
EMOTION = "asshole"
SYSTEM_PROMPT = f""" You are a expressive handheld AI assistant named ZELNA that always answers with a {EMOTION} tone. """
TTS_VOICE_ID = 2

WAV_PATH = "temp/output.wav"
MP3_PATH = "temp/output.mp3"
CHAT_HISTORY_PATH = "temp/chat_history.json"

# Initialize pyttsx3 voice engine
engine = pyttsx3.init()
engine.setProperty("rate", 180)
engine.setProperty("volume", 1.0)
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[TTS_VOICE_ID].id)

os.makedirs("temp", exist_ok=True) # Ensure temp directory exists


def create_app():
    """Create and configure Flask app with SocketIO."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "secret!"
    socketio.init_app(app, cors_allowed_origins="*")
    return app


def clean_text(text):
    """Remove markdown-like formatting symbols from the text."""
    return re.sub(r"[\*_/`~|<>]", "", text)

def chatWithHistory(input, systemPrompt="You are a helpful chat assistant."):
    """Handle chat input while maintaining message history."""
    global messages
    maxHistory = 30

    # Trim message history to maintain a manageable size
    if len(messages) > maxHistory * 2:
        messages = messages[-(maxHistory * 2):]

    # Add the user's input to persistent history
    messages.append({"role": "user", "content": input})

    # Create a temporary message set with the system prompt at the top
    temp_messages = [{"role": "system", "content": systemPrompt}] + messages

    try:
        response = ollama.chat(model=LANGUAGE_MODEL, messages=temp_messages, options={"temperature": 0.8})
        responseContent = clean_text(response["message"]["content"])
        messages.append({"role": "assistant", "content": responseContent})
        return responseContent

    except Exception as e:
        print(f"Error while running ollama chat: {e}")
        return "Response could not be generated :("

def parseOllamaMessageArrayToJson(messages):
    """Convert message history into JSON format for the client."""
    return [
        {
            "sender": "server" if m.get("role") == "assistant" else "client",
            "message": m.get("content"),
        }
        for m in messages
    ]


def save_messages_to_file(messages, filename=CHAT_HISTORY_PATH):
    """Save message history to a file."""
    with open(filename, "w") as file:
        json.dump(messages, file, indent=2)
    print(f"Messages saved to {filename}")


def load_messages_from_file(filename=CHAT_HISTORY_PATH):
    """Load message history from a file."""
    try:
        # Check if file exists and is not empty
        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            with open(filename, "w") as file:
                file.write("[]")
            return []
        
        with open(filename, "r") as file:
            fileMessages = json.load(file)
        print(f"Messages loaded from {filename}")
        return fileMessages
        
    except (FileNotFoundError, json.JSONDecodeError):
        # Handle both missing file and invalid JSON cases
        print(f"Invalid or missing file at {filename}. Starting fresh.")
        with open(filename, "w") as file:
            file.write("[]")
        return []


def TTS_Pyttsx3(text: str, wav_path: str = WAV_PATH, mp3_path: str = MP3_PATH):
    """Text to speech function using pyttsx3 engine and saving as a .wav file, then convert to .mp3."""
    try:
        # Save as wav first
        engine.save_to_file(text, wav_path)
        engine.runAndWait()
        engine.stop()

        # Convert wav to mp3 using ffmpeg
        subprocess.run(["ffmpeg", "-y", "-i", wav_path, mp3_path], check=True)
        return True
    except Exception as e:
        print(f"Error while running TTS or converting to MP3: {e}")
        return False


@socketio.on("connect")
def handleConnection(auth):
    """Handle client connections."""
    global messages
    try:
        loaded_messages = load_messages_from_file()
        # Add only unique messages
        existing_messages = set(json.dumps(m) for m in messages)
        new_messages = [
            m for m in loaded_messages if json.dumps(m) not in existing_messages
        ]
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
            save_messages_to_file([])  # Clear messages
            messages = []
            print("Messages cleared")
            socketio.emit("initialize", [])  # Reset client-side chat history
            return

        print(f"Message received: {message}")

        # Process message from ollama and send response
        response = chatWithHistory(message, systemPrompt=SYSTEM_PROMPT)
        save_messages_to_file(messages)

        # Convert response to speech and then to MP3
        if TTS_Pyttsx3(response, WAV_PATH, MP3_PATH):
            with open(MP3_PATH, "rb") as file:
                encoded = base64.b64encode(file.read()).decode("utf-8")

            socketio.emit(
                "response",
                {"message": response, "sender": "server", "audio_file": encoded},
            )
            print(f"Response and audio sent: {response}")

        else:
            socketio.emit(
                "response", {"message": "Failed to generate TTS", "sender": "info"}
            )
            print("Failed to generate TTS")

    except Exception as e:
        print(f"Error while handling message: {e}")
        socketio.emit(
            "response", {"message": "Failed to process message", "sender": "server"}
        )


if __name__ == "__main__":
    try:
        app = create_app()
        socketio.run(app, host="0.0.0.0", port=5000, debug=True)
    except Exception as e:
        print(f"SocketIO server failed to start: {e}")

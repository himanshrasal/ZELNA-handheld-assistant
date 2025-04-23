import sys, time, socketio, sounddevice, queue, json, base64, os, subprocess, tempfile, threading

# Import GPIO library based on platform
if sys.platform == "win32":
    from FakeGPIO import GPIO
else:
    import RPi.GPIO as GPIO

from vosk import Model, KaldiRecognizer
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout
from widgets.ChatBox import ChatBox
from widgets.MessageBox import MessageBox
from resources.Theme import UI

# Define constant for placeholder text
PLACEHOLDER_TEXT = " ( > w < ) "

# initialize socketio client
sio = socketio.Client(
    reconnection=True,
    reconnection_attempts=-1,
    reconnection_delay=1,
    reconnection_delay_max=5,
)


class mainWindow(QWidget):
    def __init__(self):
        self.ResponseGenerationActive = False
        super().__init__()
        self.initUI()
        self.initThreads()

    def initUI(self):

        self.lightMode = True  # set light mode on or off
        ui = UI(self.lightMode)

        self.setWindowTitle("ZELNA")
        self.setGeometry(0, 0, 640, 480)
        self.setStyleSheet(f"""background-color:{ui.windowBackground}; border: none;""")
        self.setCursor(Qt.BlankCursor)

        layout = QVBoxLayout()

        self.chatBox = ChatBox(lightmode=self.lightMode)

        self.messageBox = MessageBox(lightmode=self.lightMode)
        self.messageBox.setFixedHeight(80)

        layout.addWidget(self.chatBox)
        layout.addWidget(self.messageBox)
        self.setLayout(layout)

        self.messageBox.updateText(PLACEHOLDER_TEXT)

    def initThreads(self):
        # Initialize threads
        self.socketThread = SocketThread()
        self.gpioThread = GPIOThread()
        self.speechToTextThread = SpeechToTextThread()
        self.textToSpeechThread = TextToSpeechThread()

        # Connect the signal to a slot method in mainWindow
        self.socketThread.socketSignal.connect(self.handleSocket)
        self.gpioThread.gpioSignal.connect(self.handleGpio)
        self.speechToTextThread.sttSignal.connect(self.handleStt)
        self.textToSpeechThread.ttsSignal.connect(self.handleTts)

        self.socketThread.start()
        self.gpioThread.start()
        self.speechToTextThread.start()
        self.textToSpeechThread.start()

    def closeEvent(self, event):
        self.socketThread.quit()
        self.gpioThread.quit()
        self.speechToTextThread.quit()
        self.textToSpeechThread.quit()

        event.accept()

    # callbacks
    def handleSocket(self, eventName, data):
        if eventName == "initialize":
            self.chatBox.clearMessages()
            self.chatBox.initMessages(data)
            self.setResponseGenerationActive(False)

        if eventName == "message":
            self.chatBox.addMessage(data.get("message"), data.get("sender"))

        if eventName == "response":
            self.chatBox.addMessage(data.get("message"), data.get("sender")) #send message to chatbox
            
            audio_file = data.get("audio_file")       # get and play audio file from server
            if audio_file:
                self.textToSpeechThread.play_audio(audio_file)

            self.setResponseGenerationActive(False)
        
    def handleGpio(self, eventName):
        if eventName == "powerButtonPressed":
            if self.textToSpeechThread.is_playing_audio():
                self.textToSpeechThread.stop_playback()
                time.sleep(0.1)
            
            if not self.ResponseGenerationActive:
                self.speechToTextThread.isListening = True

        if eventName == "powerButtonReleased":
            self.speechToTextThread.isListening = False

        if eventName == "upButton":
            self.chatBox.scrollUp(duration=100, scrollAmount=300)

        if eventName == "downButton":
            self.chatBox.scrollDown(duration=100, scrollAmount=300)

    def handleStt(self, eventName, data):
        if eventName == "message":
            self.chatBox.addMessage(data.get("message"), "info")

        if eventName == "partialResult":
            if not self.ResponseGenerationActive:
                self.messageBox.updateText(data.get("message"))

        if eventName == "finalResult":
            self.messageBox.updateText(data.get("message"))
            self.chatBox.addMessage(data.get("message"), "client")
            self.emitToServer("message", data.get("message"))
            
    def handleTts(self, eventName, data):
        if eventName == "error":
            self.messageBox.updateText(data.get("message"))

    def emitToServer(self, eventName, message):
        retry = True
        reported = False
        tries = 3
        
        while retry and tries > 0:
            if sio.connected:
                try:
                    self.setResponseGenerationActive(True)
                    sio.emit(eventName, message)
                    retry = False
                except Exception as e:
                    tries -= 1
                    if not reported:
                        self.chatBox.addMessage(
                            f"Failed to send message: {str(e)}",
                            "info",
                        )
                        reported = True
            else:
                tries -= 1
                if not reported:
                    self.chatBox.addMessage(
                        "Couldn't send prevoius message.\nMake sure the server is running.",
                        "info",
                    )
                    self.setResponseGenerationActive(False)
                    reported = True
                    

    def setResponseGenerationActive(self, value: bool):
        self.ResponseGenerationActive = value
        if value:
            self.messageBox.updateText("Response is being generated ...")
        else:
            self.messageBox.updateText(PLACEHOLDER_TEXT)


# QThread classes for handling sockets and GPIO in separate


class SocketThread(QThread):
    socketSignal = pyqtSignal(str, object)

    def run(self):
        port = "http://192.168.0.101:5000"
        retry_delay = 5  # seconds between retries

        @sio.on("initialize")
        def handleInitialization(data):
            self.socketSignal.emit("initialize", data)

        @sio.on("disconnect")
        def handleDisconnection():
            self.socketSignal.emit(
                "message",
                {"message": "Disconnected from server", "sender": "info"},
            )

        @sio.on("response")
        def handleMessage(data):
            self.socketSignal.emit("response", data)

        while True:
            try:

                sio.connect(
                    port,
                    transports=["websocket"],
                    auth={"token": "zelnaAuthentication"},
                    retry=True,
                )
                sio.wait()

            except Exception as e:
                self.socketSignal.emit(
                    "message",
                    {
                        "message": f"Couldn't connect to the server. Retrying in {retry_delay} seconds...",
                        "sender": "info",
                    },
                )
                time.sleep(retry_delay)


class GPIOThread(QThread):
    gpioSignal = pyqtSignal(str)

    def run(self):
        try:
            # pins
            powerPin = 26
            powerPinPressed = False

            upPin = 6
            upPinPressed = False

            downPin = 5
            downPinPressed = False

            GPIO.setmode(GPIO.BCM)
            GPIO.setup(powerPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(upPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(downPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            while True:
                # Power Pin
                if not GPIO.input(powerPin):
                    if not powerPinPressed:
                        self.gpioSignal.emit("powerButtonPressed")
                        powerPinPressed = True
                else:
                    if powerPinPressed:
                        self.gpioSignal.emit("powerButtonReleased")
                    powerPinPressed = False

                # up / down pin interrupts
                if not GPIO.input(upPin):
                    if not upPinPressed:
                        self.gpioSignal.emit("upButton")
                        upPinPressed = True
                else:
                    upPinPressed = False

                if not GPIO.input(downPin):
                    if not downPinPressed:
                        self.gpioSignal.emit("downButton")
                        downPinPressed = True
                else:
                    downPinPressed = False

                time.sleep(0.05)

        except Exception as e:
            self.gpioSignal.emit("message", {"message": f"An error occurred: {str(e)}"})
        finally:
            GPIO.cleanup()

class SpeechToTextThread(QThread):
    sttSignal = pyqtSignal(str, object)

    def __init__(self):
        super().__init__()
        self.queue = queue.Queue()
        self.isListening = False
        self.resetRequested = False
        self.model = Model(model_name="vosk-model-small-en-us-0.15")
        self.samplerate = None

        self.prevPartialText = ""
        self.finalText = ""
        self.lastWord = ""

    def callback(self, indata, frames, time, status):
        if self.isListening:
            self.queue.put(bytes(indata))

    def run(self):
        try:
            device_info = sounddevice.query_devices(None, "input")
            self.samplerate = int(device_info["default_samplerate"])

            with sounddevice.RawInputStream(
                samplerate=self.samplerate,
                blocksize=2048,
                device=None,
                dtype="int16",
                channels=1,
                callback=self.callback,
            ):
                self.rec = KaldiRecognizer(self.model, self.samplerate)

                while True:
                    if self.resetRequested:
                        self.resetProperties()
                        self.resetRequested = False

                    if self.isListening:
                        if not self.queue.empty():
                            data = self.queue.get()

                            if self.rec.AcceptWaveform(data):
                                result = json.loads(self.rec.Result())
                                finalText = result.get("text", "").strip()

                                if finalText:
                                    if self.finalText and not self.finalText.endswith(" "):
                                        self.finalText += " "
                                    self.finalText += finalText
                                    self.prevPartialText = ""
                                    self.lastWord = finalText.split()[-1] if finalText else ""

                            else:
                                partialResult = json.loads(self.rec.PartialResult()).get("partial", "").strip()

                                if partialResult != self.prevPartialText:
                                    combinedText = self.finalText
                                    if self.finalText and (partialResult and not partialResult.startswith(self.lastWord)):
                                        combinedText += " "
                                    combinedText += partialResult

                                    self.sttSignal.emit("partialResult", {"message": combinedText.strip()})
                                    self.prevPartialText = partialResult

                    else:
                        if self.finalText and not self.resetRequested:
                            self.sttSignal.emit("finalResult", {"message": self.finalText.strip()})
                            
                        # Ensure partial text on screen is cleared even if no final text
                        self.sttSignal.emit("partialResult", {"message": PLACEHOLDER_TEXT})
                        
                        if not self.resetRequested:
                            self.requestReset()

        except Exception as e:
            self.sttSignal.emit("message", {"message": f"An error occurred: {str(e)}"})

    def resetProperties(self):
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break
        self.rec = KaldiRecognizer(self.model, self.samplerate)
        self.prevPartialText = ""
        self.finalText = ""
        self.lastWord = ""

    def requestReset(self):
        self.resetRequested = True

class TextToSpeechThread(QThread):
    ttsSignal = pyqtSignal(str, object)
    
    def __init__(self):
        super().__init__()
        # Check if mpg123 is installed
        if not self._check_mpg123_installed():
            self.ttsSignal.emit("error", {"message": "mpg123 not installed. Please run: sudo apt-get install mpg123"})
            
        self.current_process = None
        self.lock = threading.Lock()
        self.is_playing = False
        self.audio_file = os.path.join(os.getcwd(), "qtApp/current_audio.mp3")
    
    def _check_mpg123_installed(self):
        """Check if mpg123 is available in system PATH"""
        try:
            return subprocess.call(['which', 'mpg123'], 
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL) == 0
        except:
            return False
    
    def play_audio(self, base64_audio):
        """Play audio using file in working directory"""
        with self.lock:
            self._stop_playback()
            
            try:
                # Write decoded audio to file
                with open(self.audio_file, 'wb') as f:
                    f.write(base64.b64decode(base64_audio))
                
                # Start playback
                self.is_playing = True
                self.current_process = subprocess.Popen(
                    ['mpg123', '-q', self.audio_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                # Monitor playback completion
                threading.Thread(
                    target=self._monitor_playback,
                    daemon=True
                ).start()
                
            except Exception as e:
                self.is_playing = False
                self.ttsSignal.emit("error", {
                    "message": f"Playback failed: {str(e)}"
                })
                self._cleanup_file()
    
    def _monitor_playback(self):
        """Wait for playback completion and clean up"""
        try:
            if self.current_process:
                self.current_process.wait(timeout=1800)  # 30 minute max
        finally:
            with self.lock:
                self.is_playing = False
            self._cleanup_file()
    
    def _stop_playback(self):
        """Force stop current playback"""
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=0.5)
            except:
                try:
                    self.current_process.kill()
                except:
                    pass
            finally:
                self.current_process = None
                self.is_playing = False
                self._cleanup_file()
    def stop_playback(self):
        """Public method to stop playback safely"""
        with self.lock:
            self._stop_playback()

    
    def _cleanup_file(self):
        """Remove the audio file if it exists"""
        try:
            if os.path.exists(self.audio_file):
                os.remove(self.audio_file)
        except:
            pass
    
    def is_playing_audio(self):
        """Thread-safe playback status check"""
        with self.lock:
            return self.is_playing

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = mainWindow()
    window.show()

    sys.exit(app.exec_())

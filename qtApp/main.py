import sys, time, socketio, sounddevice, queue, json

# Import GPIO library based on platform
if sys.platform == "win32":
    from FakeGPIO import GPIO
else:
    import RPi.GPIO as GPIO

from vosk import Model, KaldiRecognizer
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout
from widgets.ChatBox import ChatBox
from widgets.MessageBox import MessageBox
from resources.Theme import UI

# initialize socketio client
sio = socketio.Client(
    reconnection=True,
    reconnection_attempts=-1,
    reconnection_delay=1,
    reconnection_delay_max=5,
)


class mainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initThreads()

    def initUI(self):
        self.lightMode = True  # set light mode on or off
        ui = UI(self.lightMode)

        self.setWindowTitle("ZELNA")
        self.setGeometry(0, 0, 640, 480)
        self.setStyleSheet(f"""background-color:{ui.windowBackground}; border: none;""")

        layout = QVBoxLayout()

        self.chatBox = ChatBox(lightmode=self.lightMode)

        self.messageBox = MessageBox(lightmode=self.lightMode)
        self.messageBox.setFixedHeight(80)

        layout.addWidget(self.chatBox)
        layout.addWidget(self.messageBox)
        self.setLayout(layout)

        self.messageBox.updateText("Your text will appear here")

    def initThreads(self):
        # Initialize threads
        self.socketThread = SocketThread()
        self.gpioThread = GPIOThread()
        self.SpeechToTextThread = SpeechToText()

        # Connect the signal to a slot method in mainWindow
        self.socketThread.socketSignal.connect(self.handleSocket)
        self.gpioThread.gpioSignal.connect(self.handleGpio)
        self.SpeechToTextThread.sttSignal.connect(self.handleStt)

        self.socketThread.start()
        self.gpioThread.start()
        self.SpeechToTextThread.start()

    def closeEvent(self, event):
        self.socketThread.quit()
        self.gpioThread.quit()
        self.SpeechToTextThread.quit()

        # Wait for threads to finish
        self.socketThread.wait()
        self.gpioThread.wait()
        self.SpeechToTextThread.wait()

        event.accept()

    # callbacks
    def handleSocket(self, eventName, data):
        if eventName == "initialize":
            self.chatBox.clearMessages()
            self.chatBox.initMessages(data)

        if eventName == "message":
            self.chatBox.addMessage(data.get("message"), data.get("sender"))

    def handleGpio(self, eventName):
        if eventName == "powerButtonPressed":
            self.SpeechToTextThread.isListening = True

        if eventName == "powerButtonReleased":
            self.SpeechToTextThread.isListening = False
            time.sleep(0.03)  # allow any ongoing callback to finish
            self.SpeechToTextThread.resetRecognizer()
            self.SpeechToTextThread.clearQueue()

        if eventName == "volumeUpButton":
            self.chatBox.scrollUp()

        if eventName == "volumeDownButton":
            self.chatBox.scrollDown()

    def handleStt(self, eventName, data):
        if eventName == "message":
            self.chatBox.addMessage(data.get("message"), "info")

        if eventName == "partialResult":
            self.messageBox.updateText(data.get("message"))

        if eventName == "finalResult":
            self.emitToServer("message", data.get("message"))
            self.chatBox.addMessage(data.get("message"), "user")
            self.messageBox.updateText("Your text will appear here")

    def emitToServer(self, eventName, message):
        retry = True
        reported = False
        tries = 3
        while retry and tries > 0:
            if sio.connected:
                try:
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
                        "Couldn't send message.\nMake sure the server is running.",
                        "info",
                    )
                    reported = True


# QThread classes for handling sockets and GPIO in separate


class SocketThread(QThread):
    socketSignal = pyqtSignal(str, object)

    def run(self):
        port = "http://192.168.0.101:5000"
        retry_delay = 5  # seconds between retries

        while True:
            try:

                @sio.on("initialize")
                def handleInitialization(data):
                    self.socketSignal.emit("initialize", data)

                @sio.on("disconnect")
                def handleDisconnection():
                    self.socketSignal.emit(
                        "message",
                        {"message": "Disconnected from server", "sender": "info"},
                    )

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
            powerPin = 5
            powerPinPressed = False

            volumeUpPin = 6
            volumeUpPinPressed = False

            GPIO.setmode(GPIO.BCM)
            GPIO.setup(powerPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(volumeUpPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

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

                # volume pin interrupts
                if not GPIO.input(volumeUpPin):
                    if not volumeUpPinPressed:
                        self.gpioSignal.emit("volumeUpButton")
                        volumeUpPinPressed = True
                else:
                    volumeUpPinPressed = False

                time.sleep(0.05)

        except Exception as e:
            self.gpioSignal.emit("message", {"message": f"An error occurred: {str(e)}"})
        finally:
            GPIO.cleanup()


class SpeechToText(QThread):
    sttSignal = pyqtSignal(str, object)

    def __init__(self):
        super().__init__()
        self.queue = queue.Queue()
        self.isListening = False
        self.model = Model(model_name="vosk-model-small-en-us-0.15")  # Load model once
        self.samplerate = None

        self.prevPartialText = ""
        self.finalText = ""

    def callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        # if status:
        #     print(status, file=sys.stderr)
        if self.isListening:  # Only add data to the queue if listening
            self.queue.put(bytes(indata))

    def run(self):
        """Main thread loop for processing audio."""
        try:
            # Set default sampling rate and device
            device_info = sounddevice.query_devices(None, "input")
            self.samplerate = int(device_info["default_samplerate"])

            # Start audio stream
            with sounddevice.RawInputStream(
                samplerate=self.samplerate,
                blocksize=4000,  # Smaller blocksize for lower latency
                device=None,
                dtype="int16",
                channels=1,
                callback=self.callback,
            ):
                self.rec = KaldiRecognizer(self.model, self.samplerate)

                while True:
                    if self.isListening:
                        if not self.queue.empty():
                            data = self.queue.get()

                            if self.rec.AcceptWaveform(data):  # final text
                                result = self.rec.Result()
                                finalText = json.loads(result).get("text", "")
                                if finalText:
                                    self.finalText = self.finalText + " " + finalText

                            else:  # partial text
                                partialResult = json.loads(
                                    self.rec.PartialResult()
                                ).get("partial", "")
                                if (
                                    partialResult
                                    and not partialResult == self.prevPartialText
                                ):
                                    self.sttSignal.emit(
                                        "partialResult",
                                        {
                                            "message": f"{self.finalText} {partialResult}"
                                        },
                                    )
                                    self.prevPartialText = partialResult
                    else:
                        # reutrn if no partial or final result is available
                        if not self.prevPartialText and not self.finalText:
                            # Sleep to reduce CPU usage when not listening
                            time.sleep(0.1)
                            continue

                        # send partial result if final result is not available but partial result is available
                        if self.prevPartialText and not self.finalText:
                            self.sttSignal.emit(
                                "finalResult", {"message": self.prevPartialText}
                            )

                        # send final + partial result if final and partial result is available
                        if self.prevPartialText and self.finalText:
                            # self.finalText = self.finalText + " " + self.prevPartialText
                            self.sttSignal.emit(
                                "finalResult", {"message": self.finalText.strip()}
                            )

                        # reset variables at end of listening
                        if self.prevPartialText or self.finalText:
                            # reset variables
                            self.prevPartialText = ""
                            self.finalText = ""

        except Exception as e:
            self.sttSignal.emit("message", {"message": f"An error occurred: {str(e)}"})

    def clearQueue(self):
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break
        # force reset variables just in case
        self.prevPartialText = ""
        self.finalText = ""

    def resetRecognizer(self):
        self.rec = KaldiRecognizer(self.model, self.samplerate)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = mainWindow()
    window.show()

    sys.exit(app.exec_())

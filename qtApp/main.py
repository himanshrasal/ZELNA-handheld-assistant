import sys, time, socketio, sounddevice, queue, json

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

        self.messageBox.updateText("  ( > w < )  ")

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

        # # Wait for threads to finish
        # self.socketThread.wait()
        # self.gpioThread.wait()
        # self.SpeechToTextThread.wait()

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
            self.chatBox.addMessage(data.get("message"), data.get("sender"))
            self.setResponseGenerationActive(False)

    def handleGpio(self, eventName):
        if eventName == "powerButtonPressed":
            if not self.ResponseGenerationActive:
                self.SpeechToTextThread.isListening = True

        if eventName == "powerButtonReleased":
            self.SpeechToTextThread.isListening = False

        if eventName == "upButton":
            self.chatBox.scrollUp()

        if eventName == "downButton":
            self.chatBox.scrollDown()

    def handleStt(self, eventName, data):
        if eventName == "message":
            self.chatBox.addMessage(data.get("message"), "info")

        if eventName == "partialResult":
            self.messageBox.updateText(data.get("message"))

        if eventName == "finalResult":
            self.messageBox.updateText(data.get("message"))
            self.chatBox.addMessage(data.get("message"), "client")
            self.emitToServer("message", data.get("message"))

    def emitToServer(self, eventName, message):
        retry = True
        reported = False
        tries = 3
        while retry and tries > 0:
            if sio.connected:
                try:
                    sio.emit(eventName, message)
                    self.setResponseGenerationActive(True)
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
            self.messageBox.updateText("Response is being generated")
        else:
            self.messageBox.updateText(" ( > w < ) ")


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

                @sio.on("response")
                def handleMessage(message):
                    self.socketSignal.emit("response", message)

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

class SpeechToText(QThread):
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
                            self.finalText = ""
                            self.prevPartialText = ""
                            self.lastWord = ""

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = mainWindow()
    window.show()

    sys.exit(app.exec_())
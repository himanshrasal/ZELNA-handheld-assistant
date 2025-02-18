import sys, time, socketio, sounddevice, queue, json

import sys

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

sio = socketio.Client()

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

        # Adding chat messages for testing:

        self.chatBox.initMessages(testdata)

        self.messageBox.updateText("Thank you!")

    def initThreads(self):
        # Initialize threads
        self.socketThread = SocketThread()
        self.gpioThread = GPIOThread()
        self.SpeechToTextThread = SpeechToText()

        # Connect the signal to a slot method in mainWindow
        self.socketThread.socketSignal.connect(self.handleSocket)
        self.gpioThread.gpioSignal.connect(self.handleGpio)
        self.SpeechToTextThread.sttSignal.connect(self.handleStt)

        # connecting gpio signal to speech to text
        # self.gpioThread.gpioSignal.connect(self.SpeechToTextThread.handleGpioSignal)

        self.socketThread.start()
        self.gpioThread.start()
        self.SpeechToTextThread.start()

    # callbacks
    def handleSocket(self, eventName, data):
        if eventName == "initialize":
            self.chatBox.clearMessages()
            print("messages cleared")
            self.chatBox.initMessages(data)
            print("initialized")
        if eventName == "message":
            self.chatBox.addMessage(data.get("message"), data.get("sender"))

    def handleGpio(self, eventName):
        if eventName == "powerButtonPressed":
            self.chatBox.addMessage("Power button pressed", "info")
            self.SpeechToTextThread.isListening = True

        if eventName == "powerButtonReleased":
            self.chatBox.addMessage("Power button released", "info")
            self.SpeechToTextThread.isListening = False

        if eventName == "volumeUpButton":
            self.chatBox.scrollUp()
        if eventName == "volumeDownButton":
            self.chatBox.scrollDown()

    def handleStt(self, eventName, data):
        if eventName == "message":
            self.chatBox.addMessage(data.get("message"), "info")


# threads


class SocketThread(QThread):
    socketSignal = pyqtSignal(str, object)

    def run(self):
        port = "http://192.168.0.101:5000"

        try:

            @sio.on("initialize")
            def handleInitialization(data):
                print("Received data from server")
                self.socketSignal.emit(
                    "initialize", data
                )  # Emit signal to main thread when data is received

            sio.connect(
                port,
                transports=["websocket"],
                auth={"token": "zelnaAuthentication"},
                retry=True,
            )

            sio.wait()
        except Exception as e:
            print(f"Socket.IO connection error: {e}")
            self.socketSignal.emit(
                "message",
                {
                    "message": f"Couldn't connect to the server.\nMake sure the server is running at port: {port}",
                    "sender": "info",
                },
            )


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
            print(f"GPIO error: {e}")

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

    def handleGpioSignal(self, eventName):
        """Handle power button events from GPIO thread."""
        if eventName == "powerButtonPressed":
            if not self.isListening:
                self.isListening = True
                self.start()  # Start the QThread
        elif eventName == "powerButtonReleased":
            self.isListening = False  # Stop listening on button release

    def callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
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
                blocksize=8000,  # Smaller blocksize for lower latency
                device=None,
                dtype="int16",
                channels=1,
                callback=self.callback,
            ):
                print("Microphone activated. Listening...")
                rec = KaldiRecognizer(self.model, self.samplerate)
                self.sttSignal.emit("message", {"message":"Microphone activated. Listening..."})

                while True:
                    if not self.queue.empty() and self.isListening:
                        data = self.queue.get()
                        if rec.AcceptWaveform(data):
                            result = rec.Result()
                            print("Final Result:", result)
                            self.sttSignal.emit("message", {"message": str(json.loads(result).get('text'))})
                        else:
                            partial_result = rec.PartialResult()
                            print("Partial Result:", partial_result)
                            res = str(json.loads(rec.PartialResult()).get("partial"))
                            if res != None:
                                self.sttSignal.emit("message", {"message": res})

        except Exception as e:
            print("An error occurred:", str(e))
            self.sttSignal.emit("message", {"message":f"An error occurred: {str(e)}"})


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = mainWindow()
    window.show()

    sys.exit(app.exec_())

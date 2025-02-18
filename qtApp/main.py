import sys
import time
import RPi.GPIO as GPIO
import socketio
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
        self.gpioThread = GpioThread()

        # Connect the signal to a slot method in mainWindow
        self.socketThread.socketSignal.connect(self.handleSocket)
        self.gpioThread.gpioSignal.connect(self.handleGpio)

        self.socketThread.start()
        self.gpioThread.start()

    #callbacks
    def handleSocket(self, eventName, data):
        if eventName == "initialize":
            self.chatBox.clearMesages()
            print("messages cleared")
            self.chatBox.initMessages(data)
            print("initialized")
        if eventName == "message":
            self.chatBox.addMessage(data.get("message"), data.get("sender"))
            
    def handleGpio(self, eventName):
        if eventName == "powerButton":
            self.chatBox.addMessage("Power button pressed", "info")
        
        if eventName == "volumeUpButton":
            self.chatBox.scrollUp()
            
        if eventName == "volumeDownButton":
            self.chatBox.scrollDown()

#threads 

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
            self.socketSignal.emit("message", {"message":f"Couldn't connect to the server.\nMake sure the server is running at port: {port}", "sender":"info"})

class GpioThread(QThread):
    gpioSignal = pyqtSignal(str)
    
    def run(self):
        try:
            #pins
            powerPin = 5
            powerPinPressed = False
            
            volumeUpPin = 6
            volumeUpPinPressed = False
                    
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(powerPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(volumeUpPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            while True:
                # Power Pin Interrupt
                if not GPIO.input(powerPin):
                    if not powerPinPressed:
                        self.gpioSignal.emit("powerButton")
                        powerPinPressed = True
                else:
                    powerPinPressed = False
                
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
        
    #callbacks
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = mainWindow()
    window.show()

    sys.exit(app.exec_())

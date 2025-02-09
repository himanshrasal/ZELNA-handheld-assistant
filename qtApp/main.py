import sys
import socketio
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout
from widgets.ChatBox import ChatBox
from widgets.MessageBox import MessageBox
from resources.Theme import UI

sio = socketio.Client()


class SocketThread(QThread):
    eventSignal = pyqtSignal(str, object)

    def run(self):
        try:

            @sio.on("initialize")
            def handleInitialization(data):
                print("Received data from server")
                self.eventSignal.emit(
                    "initialize", data
                )  # Emit signal to main thread when data is received

            sio.connect("http://localhost:5000", auth={"token": "maza auth hehe"})

            sio.wait()
        except Exception as e:
            print(f"Socket.IO connection error: {e}")


class mainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initSocketIO()

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
        self.chatBox.addMessage("new message not from dataset", "info")

        self.messageBox.updateText("Thank you!")

    def initSocketIO(self):
        # all events like @sio.on etc

        self.socketThread = SocketThread()

        # Connect the signal to a slot method in mainWindow
        self.socketThread.eventSignal.connect(self.handleInitialization)

        self.socketThread.start()

    def handleInitialization(self, eventName, data):
        match eventName:
            case "initialize":
                self.chatBox.clearMesages()
                print("messages cleared")
                self.chatBox.initMessages(data)
                print("initialized")
            case "message":
                self.chatBox.addMessage(data.get("message"), data.get("sender"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = mainWindow()
    window.show()

    sys.exit(app.exec_())

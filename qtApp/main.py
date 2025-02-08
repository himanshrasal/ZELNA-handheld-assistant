import sys
import socketio
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout
from widgets.ChatBox import ChatBox
from widgets.MessageBox import MessageBox
from resources.Theme import UI

testdata = [
    {"message": "1", "sender": "server"},
    {"message": "2", "sender": "client"},
    {"message": "4", "sender": "server"},
    {"message": "5", "sender": "client"},
    {"message": "6", "sender": "server"},
    {"message": "7", "sender": "client"},
    {"message": "8", "sender": "server"},
    {"message": "9", "sender": "client"},
    {"message": "10", "sender": "server"},
    {"message": "11", "sender": "client"},

]

sio = socketio.Client()

class SocketThread(QThread):
    def run(self):
        try:
            sio.connect('http://localhost:5000', auth={'token': 'maza auth hehe'})
            sio.wait()
        except Exception as e:
            print(f"Socket.IO connection error: {e}")

class mainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initSocketIO()
        
    def initUI(self):
        self.lightMode = False
        ui = UI(self.lightMode)
        
        self.setWindowTitle("ZELNA")
        self.setGeometry(0,0,640,480)
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
        self.chatBox.addMessage("new message not from dataset", "info")
        
        self.messageBox.updateText("Thank you!")
        
    def initSocketIO(self):
        #all events like @sio.on etc
        
        @sio.on('initialize')
        def handleInitialization(data):
            self.chatBox.initMessages(data)

        self.socketThread = SocketThread()
        self.socketThread.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = mainWindow()
    window.show()
    
    
    sys.exit(app.exec_())
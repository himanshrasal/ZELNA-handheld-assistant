from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QSpacerItem, QSizePolicy, QScrollArea, QApplication, QPushButton
import sys

class textBubble(QLabel):
    def __init__(self, text, color="grey"):
        super().__init__(text)
        
        self.setMaximumWidth(500)
        self.setWordWrap(True)
        self.setStyleSheet(f"""
                        font-family: "Arial";
                        font-size: 16px;
                        background-color: {color};
                        padding: 14px 12px;
                        margin: 10px;
                        border-radius: 14px;
                        """)

class textBubbleWidget(QWidget):   
    def __init__(self, text, left=False):
        super().__init__()
        
        color = "red" if left else "green"
        
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0,0,0,0)
        bubble = textBubble(text, color)
        
        if not left:
            hbox.addSpacerItem(QSpacerItem(1,1,QSizePolicy.Expanding, QSizePolicy.Preferred))

        hbox.addWidget(bubble)
        
        if left:
            hbox.addSpacerItem(QSpacerItem(1,1,QSizePolicy.Expanding, QSizePolicy.Preferred))

        self.setLayout(hbox)

class chatBox(QScrollArea):
    
    def __init__(self):
        super().__init__()
        
        self.Messages = {}
        
        self.container = QWidget()

        self.layout = QVBoxLayout(self.container)
        self.setWidget(self.container)
        self.setWidgetResizable(True)

    def add_message(self, text, left=False):
        """
        Add a message to the chatbox.
        """
        new_message = textBubbleWidget(text, left)
        self.layout.addWidget(new_message)

        # Optional: add a spacer item to push new messages upwards
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(spacer)
        
        # Ensure the chatbox scrolls to the bottom automatically after adding a message
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chat Box Example")
        self.setGeometry(100, 100, 640, 480)

        # Create chatBox instance
        self.chat_box = chatBox()

        # Create a button to add messages
        self.button = QPushButton("Add Message")
        self.button.clicked.connect(self.add_message)

        # Create the layout
        layout = QVBoxLayout()
        layout.addWidget(self.chat_box)
        layout.addWidget(self.button)

        # Set the main window's layout
        self.setLayout(layout)

    def add_message(self):
        # Adding messages to the chatbox dynamically
        self.chat_box.add_message("This is a new message!")
        self.chat_box.add_message("This message is on the left.", left=True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

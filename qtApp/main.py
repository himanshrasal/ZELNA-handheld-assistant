import sys
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout
from widgets.ChatBox import ChatBox
from widgets.MessageBox import MessageBox
from resources.Theme import UI
    
class mainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
        
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
        self.chatBox.addMessages("Hello! How can I assist you today?", True)  # AI message
        self.chatBox.addMessages("Hi! I'm having some trouble with my code.", False)  # User message
        self.chatBox.addMessages("I'd be happy to help! What seems to be the issue?", True)  # AI message
        self.chatBox.addMessages("I'm trying to implement polymorphism in Python, but I'm stuck.", False)  # User message
        self.chatBox.addMessages("Polymorphism is a great feature! Could you share your code?", True)  # AI message
        self.chatBox.addMessages("Sure, here's the code snippet...", False)  # User message
        self.chatBox.addMessages("Great, let me take a look at it. I'll guide you through it.", True)  # AI message
        self.chatBox.addMessages("Thanks! I'm looking forward to it.", False)  # User message
        self.chatBox.addMessages("No problem! Let's get it working together.", True)  # AI message
        self.chatBox.addMessages("You're awesome! Let's start.", False)  # User message
        self.chatBox.addMessages("You're welcome! Let's start by reviewing the main issues.", True)  # AI message
        self.chatBox.addMessages("bye!", True)  # AI message

        
        self.messageBox.updateText("Thank you!")
        
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = mainWindow()
    window.show()
    
    
    sys.exit(app.exec_())
import sys
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout
from widgets.ChatBox import ChatBox
from widgets.MessageBox import MessageBox
from resources.Theme import Colors
    
class mainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
        
    def initUI(self):
        self.lightMode = True
        colors = Colors(self.lightMode)
        
        self.setWindowTitle("ZELNA")
        self.setGeometry(0,0,640,480)
        self.setStyleSheet(f"""background-color:{colors.windowBackground}; border: none;""")
        
        layout = QVBoxLayout()
        
        self.chatBox = ChatBox(lightmode=self.lightMode)
    
        self.messageBox = MessageBox(lightmode=self.lightMode)
        self.messageBox.setFixedHeight(80)
        
        layout.addWidget(self.chatBox)
        layout.addWidget(self.messageBox)
        
        
        
        
        self.setLayout(layout)
        
        self.chatBox.addMessages("jfajafa",False)
        self.chatBox.addMessages("jfajafajfajafajfajafajfajafa",True)
        self.chatBox.addMessages("jfajafajfajafajfajafa",False)
        self.chatBox.addMessages("jfajafa",False)
        self.chatBox.addMessages("jfajfafasdf af af afdasfdsafafa",True)
        self.chatBox.addMessages("jfajafa",False)
        self.chatBox.addMessages("jfajafajfajafajfajafajfajafa",True)
        self.chatBox.addMessages("jfajafajfajafajfajafa",False)
        self.chatBox.addMessages("jfajafa",False)
        self.chatBox.addMessages("jfajfafasdf af af afdasfdsafafa",True)
        
        self.messageBox.updateText(" jakjfl akjfl;ka ljal kjal; j;lak jl;k;ka ljal kjal; j;lak jl;k;ka ljal kjal; j;lak jl;k;ka ljal kjal; j;lak jl;k;ka ljal kjal; j;lak jl;k;ka ljal kjal; j;lak jl;k;ka ljal kjal; j;lak jl;ka jakjfl akjfl;ka ljal kjal; j;lak jl;k;ka ljal kjal; j;lak jl;k;ka ljal kjal; j;lak jl;k;ka ljal kjal; j;lak jl;k;ka ljal kjal; j;lak jl;k;ka ljal kjal; j;lak jl;k;ka ljal kjal; j;lak jl;ka jakjfl akjfl;ka ljal kjal; j;lak jl;k;ka ljal kjal; j;lak jl;k;ka ljal kjal; j;lak jl;k;ka ljal kjal; j;lak jl;k;ka ljal kjal; j;lak jl;k;ka ljal kjal; j;lak jl;k;ka ljal kjal; j;lak jl;ka jakj")
        
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = mainWindow()
    window.show()
    sys.exit(app.exec_())
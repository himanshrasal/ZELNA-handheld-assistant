from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QSpacerItem, QSizePolicy, QScrollArea, QGraphicsDropShadowEffect
from PyQt5.QtCore import QTimer , Qt
from PyQt5.QtGui import QColor
from resources.Theme import Colors, UI

class ChatBox(QScrollArea):
    
    def __init__(self, lightmode=False):
        super().__init__()
        self.lightmode = lightmode
        self.ui = UI(lightmode=self.lightmode)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)    
        
        self.container = QWidget()
        self.container.setStyleSheet("border:none; background:none;")

        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        
        self.setStyleSheet(f"{self.ui.chatBorders}") #scroll window styles

        self.layout.addSpacerItem(QSpacerItem(1, 1, QSizePolicy.Preferred, QSizePolicy.Expanding))
        


    #temp
    def addMessages(self, text = "", left=False):
        newMessage = TextBubbleWidget(text, left, self.lightmode)
        self.layout.insertWidget(self.layout.count() - 1, newMessage)
        
        QTimer.singleShot(0, self.scrollToBottom)


    def scrollToBottom(self):
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        
class TextBubble(QLabel):
    def __init__(self, text, color):
        super().__init__(text)
        
        self.setMaximumWidth(500)
        self.setWordWrap(True)
        self.setStyleSheet(f"""
                        font-family: "Arial";
                        font-size: 26px;
                        background-color: {color};
                        padding: 14px 12px;
                        margin: 10px;
                        border-radius: 14px;
                        """)
        self.blur = QGraphicsDropShadowEffect(self)
        self.blur.setBlurRadius(15)  # Shadow blur radius
        self.blur.setColor(QColor(220,220,255,255))  # Shadow color rgba     
        self.blur.setOffset(0, 0)  # Shadow offset (x, y)
        self.setGraphicsEffect(self.blur)


        
class TextBubbleWidget(QWidget):   
    def __init__(self, text, left=False, lightmode=False):
        super().__init__()

        color = Colors(lightmode)
        color = color.reciveBubble if left else color.sendBubble
        
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0,0,0,0)
        bubble = TextBubble(text, color)
        
        if not left:
            hbox.addSpacerItem(QSpacerItem(1,1,QSizePolicy.Expanding, QSizePolicy.Preferred))

        hbox.addWidget(bubble)
        
        if left:
            hbox.addSpacerItem(QSpacerItem(1,1,QSizePolicy.Expanding, QSizePolicy.Preferred))

        self.setLayout(hbox)
    
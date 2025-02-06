from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QSpacerItem, QSizePolicy, QScrollArea, QGraphicsDropShadowEffect
from PyQt5.QtCore import QTimer , Qt
from PyQt5.QtGui import QColor
from resources.Theme import  UI

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
        newMessage = TextBubbleWidget(text, left, lightmode=self.lightmode)
        self.layout.insertWidget(self.layout.count() - 1, newMessage)
        
        QTimer.singleShot(0, self.scrollToBottom)


    def scrollToBottom(self):
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        
class TextBubble(QLabel):
    def __init__(self, text, color, lightmode=False):
        super().__init__(text)
        
        self.lightmode = lightmode
        self.ui = UI(self.lightmode)
        
        # self.setMaximumWidth(500)  #max width for text bubble 
        self.setWordWrap(True)
        
        self.setStyleSheet(f"""
                        font-family: {self.ui.fontFamily};
                        font-size: {self.ui.fontSize};
                        color: {self.ui.fontColor};
                        background-color: {color};
                        padding: 14px 12px;
                        margin: 14px 20px;
                        border-radius: 14px;
                        """)
        
        self.blur = QGraphicsDropShadowEffect(self)
        self.blur.setBlurRadius(self.ui.bubbleBlurRadius)  # Shadow blur radius
        self.blur.setColor(QColor(*self.ui.bubbleBlurColor))  # Shadow color rgba     
        self.blur.setOffset(*self.ui.bubbleBlurOffset)  # Shadow offset (x, y)
        self.setGraphicsEffect(self.blur)


        
class TextBubbleWidget(QWidget):   
    def __init__(self, text, left=False, lightmode=False):
        super().__init__()
        self.lightmode = lightmode
        self.ui = UI(self.lightmode)
        
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0,0,0,0)
        bubble = TextBubble(text, self.ui.reciveBubble if left else self.ui.sendBubble, self.lightmode) #sets color depending on sender and reciver
        
        if not left:
            hbox.addSpacerItem(QSpacerItem(1,1,QSizePolicy.Expanding, QSizePolicy.Preferred))

        hbox.addWidget(bubble)
        
        if left:
            hbox.addSpacerItem(QSpacerItem(1,1,QSizePolicy.Expanding, QSizePolicy.Preferred))

        self.setLayout(hbox)
    
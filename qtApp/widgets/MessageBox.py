from PyQt5.QtWidgets import QScrollArea, QVBoxLayout, QLabel, QWidget, QSizePolicy
from PyQt5.QtCore import Qt, QTimer

class MessageBox(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
        
        self.setStyleSheet("""
                           background-color: #B3DEC1;
                           border: 2px solid white;
                           border-radius: 14px;
                        """)
            
        self.container = QWidget()
        self.container.setStyleSheet("border:none; background:none;")

        self.qbox = QVBoxLayout(self.container)

        self.textArea = QLabel("your text will apper here")
        self.textArea.setWordWrap(True)
        self.textArea.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.textArea.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.textArea.setStyleSheet("""
                                    font-family: "Arial";
                                    font-size: 26px;
                                    background: none;
                                    padding: 2px;
                                    margin: 0px;
                                    """)
        
        self.qbox.addWidget(self.textArea)
        
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        
    def updateText(self, text = ""):
        self.textArea.setText(text)
        QTimer.singleShot(0, self.scrollToBottom)


    def scrollToBottom(self):
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
               
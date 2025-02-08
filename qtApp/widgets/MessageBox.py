from PyQt5.QtWidgets import QScrollArea, QVBoxLayout, QLabel, QWidget, QSizePolicy
from PyQt5.QtCore import Qt, QTimer
from resources.Theme import UI


class MessageBox(QScrollArea):
    def __init__(self, lightmode=False):
        self.lightmode = lightmode
        super().__init__()
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.ui = UI(lightmode=self.lightmode)

        self.setStyleSheet(
            f"""
                           background-color: {self.ui.messageBoxBackground};
                           {self.ui.chatBorders}
                        """
        )

        self.container = QWidget()
        self.container.setStyleSheet("border:none; background:none;")

        self.qbox = QVBoxLayout(self.container)

        self.textArea = QLabel("your text will apper here")
        self.textArea.setWordWrap(True)
        self.textArea.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.textArea.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.textArea.setStyleSheet(
            f"""
                                    font-family: {self.ui.fontFamily};
                                    font-size: {self.ui.fontSize};
                                    color: {self.ui.fontColor};
                                    background: none;
                                    padding: 0px;
                                    margin: 0px;
                                    """
        )

        self.qbox.addWidget(self.textArea)

        self.setWidget(self.container)
        self.setWidgetResizable(True)

    def updateText(self, text=""):
        self.textArea.setText(text)
        QTimer.singleShot(0, self.scrollToBottom)

    def scrollToBottom(self):
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

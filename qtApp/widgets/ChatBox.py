from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QSpacerItem,
    QSizePolicy,
    QScrollArea,
    QGraphicsDropShadowEffect,
)
from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor
from resources.Theme import UI


class ChatBox(QScrollArea):
    def __init__(self, lightmode=False):
        super().__init__()
        self.lightmode = lightmode
        self.ui = UI(lightmode=self.lightmode)
        self.scrollAnimation = None  # To keep animation reference

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.container.setStyleSheet("border:none; background:none;")

        self.layout: QVBoxLayout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setWidget(self.container)
        self.setWidgetResizable(True)

        self.setStyleSheet(
            f"{self.ui.chatBorders} border-radius:{self.ui.borderRadius}"
        )

        self.layout.addSpacerItem(
            QSpacerItem(1, 1, QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        )

    # Adds a new message with smooth scroll animation
    def addMessage(self, text="", sender="info"):
        if (text == "") or (sender not in ["info", "client", "server"]):
            return

        newMessage = TextBubbleWidget(text, sender, lightmode=self.lightmode)
        self.layout.insertWidget(self.layout.count() - 1, newMessage)  # Insert before spacer

        self.container.adjustSize()  # Force layout to resize immediately
        QTimer.singleShot(0, self.scrollToBottom)  # Scroll after layout updates


    # Initializes chat with existing dataset
    def initMessages(self, dataset):
        for i in dataset:
            newMessage = TextBubbleWidget(
                i.get("message"), i.get("sender"), lightmode=self.lightmode
            )
            self.layout.addWidget(newMessage)
            QTimer.singleShot(0, self.scrollToBottom)

    # Clears all messages
    def clearMessages(self):
        while self.layout.count():
            widget = self.layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

        self.container.adjustSize() # Force layout to resize immediately

    # Smooth scroll to bottom with animation and easing
    def scrollToBottom(self, duration=500):
        self.container.adjustSize()  # Ensure proper widget resizing
        self.animateScroll(self.verticalScrollBar().maximum(), duration)


    # Smooth scroll up
    def scrollUp(self, scrollAmount=100, duration=300):
        self.animateScroll(self.verticalScrollBar().value() - scrollAmount, duration)

    # Smooth scroll down
    def scrollDown(self, scrollAmount=100, duration=300):
        self.animateScroll(self.verticalScrollBar().value() + scrollAmount, duration)

    # Generic animated scroll function
    def animateScroll(self, targetValue, duration=300):
        scrollbar = self.verticalScrollBar()
        targetValue = max(scrollbar.minimum(), min(scrollbar.maximum(), targetValue))

        animation = QPropertyAnimation(scrollbar, b"value")
        animation.setDuration(duration)
        animation.setStartValue(scrollbar.value())
        animation.setEndValue(targetValue)
        animation.setEasingCurve(QEasingCurve.OutCubic)  # Smooth cubic easing
        animation.start()

        self.scrollAnimation = animation


class TextBubble(QLabel):
    def __init__(self, text, color, lightmode=False):
        super().__init__(text)
        self.lightmode = lightmode
        self.ui = UI(self.lightmode)

        self.setMaximumWidth(1000)
        self.setWordWrap(True)

        self.setStyleSheet(
            f"""
            font-family: {self.ui.fontFamily};
            font-size: {self.ui.fontSize};
            color: {self.ui.fontColor};
            background-color: {color};
            padding: 14px 12px;
            margin: 14px 20px;
            border-radius: {self.ui.borderRadius};
            """
        )

        self.blur = QGraphicsDropShadowEffect(self)
        self.blur.setBlurRadius(self.ui.bubbleBlurRadius)
        self.blur.setColor(QColor(*self.ui.bubbleBlurColor))
        self.blur.setOffset(*self.ui.bubbleBlurOffset)
        self.setGraphicsEffect(self.blur)


class TextBubbleWidget(QWidget):
    def __init__(self, text, sender="client", lightmode=False):
        super().__init__()
        self.lightmode = lightmode
        self.ui = UI(self.lightmode)

        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)

        if sender == "client":
            bubbleColor = self.ui.sendBubble
            bubble = TextBubble(text, bubbleColor, self.lightmode)
            hbox.addSpacerItem(
                QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Preferred)
            )
            hbox.addWidget(bubble)

        if sender == "server":
            bubbleColor = self.ui.reciveBubble
            bubble = TextBubble(text, bubbleColor, self.lightmode)
            hbox.addWidget(bubble)
            hbox.addSpacerItem(
                QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Preferred)
            )

        if sender == "info":
            bubbleColor = self.ui.informationBubble
            bubble = TextBubble(text, bubbleColor, self.lightmode)
            hbox.addSpacerItem(
                QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Preferred)
            )
            hbox.addWidget(bubble)
            hbox.addSpacerItem(
                QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Preferred)
            )

        self.setLayout(hbox)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

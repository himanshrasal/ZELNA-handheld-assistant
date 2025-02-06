class Colors():
    def __init__(self, lightmode=False):
        #lightmode
        if lightmode:
            self.windowBackground = "rgb(255, 255, 255)"
            self.messageBoxBackground = "rgb(255, 222, 255)"
            self.sendBubble = "#FFD6C0"
            self.reciveBubble = "#B3DEC1"

        #darkmode
        else:
            self.windowBackground = "rgb(26, 23, 46)"
            self.messageBoxBackground = "rgb(179, 222, 193)"
            self.sendBubble = "#B3DEC1"
            self.reciveBubble = "#FFD6C0"
            
class UI:
    def __init__(self, lightmode=False):
        #lightmode
        if lightmode:
            self.chatBorders = "border: 3px solid black; border-radius: 14px;"
        #lightmode
        else:
            self.chatBorders = "border: 3px solid white; border-radius: 14px;"
class UI:
    def __init__(self, lightmode=False):
        self.fontFamily = "Arial"
        self.fontSize = "24px"
        self.borderRadius = "22px"

        # chat bubble blur
        self.bubbleBlurOffset = (0, 0)
        self.bubbleBlurRadius = 20

        # lightmode
        if lightmode:
            self.fontColor = "rgb(50, 50, 50)"
            self.chatBorders = "border: 3px solid #8AA2BF;"
            self.windowBackground = "#DAEAFF"
            self.messageBoxBackground = "#FFD6C0"

            # chat bubble
            self.sendBubble = "#B3DEC1"
            self.reciveBubble = "#FFD6C0"
            self.informationBubble = "#bbbbbb"
            # chat bubble blur
            self.bubbleBlurColor = (0, 0, 0)

        # darkmode
        else:
            self.fontColor = "#021526"
            self.chatBorders = "border: 3px solid #03346E;"
            self.windowBackground = "#001938"
            self.messageBoxBackground = "#6EACDA"

            # chat bubble
            self.sendBubble = "#6EACDA"
            self.reciveBubble = "#E2E2B6"
            self.informationBubble = "#bbbbbb"
            # chat bubble blur
            self.bubbleBlurColor = (255, 255, 255)

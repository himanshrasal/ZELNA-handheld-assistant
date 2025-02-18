import sys

class FakeGPIO:
    BCM = "BCM"
    IN = "IN"
    PUD_UP = "PUD_UP"

    def setmode(self, mode):
        print(f"GPIO mode set to {mode}")

    def setup(self, pin, mode, pull_up_down=None):
        print(f"GPIO pin {pin} set up as {mode}")

    def input(self, pin):
        return 1  # Simulate a HIGH signal (button not pressed)

    def cleanup(self):
        print("GPIO cleanup")

if sys.platform == "win32":
    GPIO = FakeGPIO()
else:
    import RPi.GPIO as GPIO

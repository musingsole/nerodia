from machine import Pin


class Nerodia:
    def __init__(self,
                 m1="P9",
                 m2="P8"):
        self.m1 = m1
        self.m2 = m2
        self.m1_pin = Pin(m1, mode=Pin.OUT)
        self.m1_pin(0)
        self.m2_pin = Pin(m2, mode=Pin.OUT)
        self.m2_pin(0)
        self.state = None
        self.close()

    def open(self):
        self.state = "OPEN"
        self.m2_pin(0)
        self.m1_pin(1)

    def close(self):
        self.state = "CLOSED"
        self.m1_pin(0)
        self.m2_pin(1)

    def __repr__(self):
        return "Nerodia is {}".format(self.state)

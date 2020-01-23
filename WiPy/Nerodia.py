from machine import Pin, reset
import json
from urequests import post
from time import sleep

from edaphic.wipy_utilities import LED_BLUE, LED_RED, LED_GREEN, LED_OFF


class Nerodia:
    def __init__(self,
                 flashing_light=None,
                 m1="P9",
                 m2="P8"):
        self.flashing_light = flashing_light
        self.m1 = m1
        self.m2 = m2
        self.m1_pin = Pin(m1, mode=Pin.OUT)
        self.m1_pin(0)
        self.m2_pin = Pin(m2, mode=Pin.OUT)
        self.m2_pin(0)
        self.state = None
        self.close()
        self.url = "https://6iexflymkg.execute-api.us-east-1.amazonaws.com/prod/heartbeat"

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

    def main(self):
        while True:
            heartbeat = {"state": self.state}
            resp = post(self.url, json=heartbeat)

            if resp.status_code != 200:
                print("Server Error: {}".format(resp.content))
                sleep(5)
                reset()

            print("Received: {}".format(resp.content))
            desired_state = resp.json()['desired_state']
            if desired_state == "OPEN":
                if self.flashing_light is not None:
                    self.flashing_light.colors = [LED_BLUE, LED_OFF, LED_GREEN] + [LED_OFF] * 10
                self.open()
            else:
                if self.flashing_light is not None:
                    self.flashing_light.colors = [LED_RED, LED_OFF, LED_GREEN] + [LED_OFF] * 10
                self.close()
            sleep(10)

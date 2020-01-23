from machine import reset
# from HTTPServer import set_wlan_to_access_point
# from edaphic.wipy_utilities import get_device_id
from edaphic.wipy_utilities import FlashingLight, LED_GREEN, LED_RED, LED_OFF, simple_connect
import time
from sys import print_exception
from Nerodia import Nerodia


if __name__ == "__main__":
    try:
        FLASHING_LIGHT = FlashingLight(colors=[LED_RED, LED_OFF], ms=250)
        print("Connecting to WiFi")
        simple_connect("noobiemcfoob", "n00biemcfoob")
        FLASHING_LIGHT.colors = [LED_GREEN] + [LED_OFF] * 10
        print("Nerodia")
        Nerodia(FLASHING_LIGHT).main()
    except Exception as e:
        print("Failed Nerodia execution")
        print_exception(e)
        time.sleep(5)
        reset()

from machine import reset
from edaphic.wipy_utilities import FlashingLight, LED_GREEN, LED_RED, LED_OFF, get_device_id, simple_connect
import time
from sys import print_exception
from HTTPServer import set_wlan_to_access_point
from NerodiaServer import nerodia_server


if __name__ == "__main__":
    try:
        FLASHING_LIGHT = FlashingLight(colors=[LED_RED, LED_OFF], ms=250)
        # print("Connecting to WiFi")
        # simple_connect()
        print("Creating Access Point")
        set_wlan_to_access_point(ssid="Nerodia_" + get_device_id(), password="nerodiapw")
        FLASHING_LIGHT.colors = [LED_GREEN] + [LED_OFF] * 10
        print("Starting Nerodia Server")
        nerodia_server()
    except Exception as e:
        print("Failed Nerodia execution")
        print_exception(e)
        time.sleep(5)
        reset()

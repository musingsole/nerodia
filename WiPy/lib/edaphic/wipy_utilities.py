import pycom
from time import sleep
import ucrypto as crypto
import machine
import os
from ubinascii import hexlify
from network import WLAN


#############################################################
# Function Name: rgbled
# Description: Provides a way to pick each color value for
# on board RGB LED
# Inputs: red, green, blue
# Outputs: None
#############################################################
def rgbled(red=0, green=0, blue=0):
    pycom.heartbeat(False)
    if red > 255:
        red = 255
    if green > 255:
        green = 255
    if blue > 255:
        blue = 255

    red = int(red) << 16
    green = int(green) << 8
    blue = int(blue)
    color = red + green + blue

    pycom.rgbled(color)
    return


LED_RED = (255, 0, 0)
LED_GREEN = (0, 255, 0)
LED_BLUE = (0, 0, 255)
LED_PURPLE = (255, 0, 255)
LED_TEAL = (0, 255, 255)
LED_YELLOW = (255, 255, 0)
LED_WHITE = (255, 255, 255)
LED_OFF = (0, 0, 0)


class FlashingLight:
    def __init__(self, ms=1000, colors=[LED_RED, LED_OFF, LED_GREEN, LED_OFF, LED_BLUE, LED_OFF]):
        self.seconds = 0
        self.colors = colors
        self.current_color_index = 0
        self.display_current_color()
        self.__alarm = machine.Timer.Alarm(handler=self.seconds_handler, ms=ms, periodic=True)

    def set_milliseconds(self, ms):
        self.__alarm.cancel()
        self.__alarm = machine.Timer.Alarm(handler=self.seconds_handler, ms=ms, periodic=True)

    def next_color(self):
        self.current_color_index += 1
        if self.current_color_index >= len(self.colors):
            self.current_color_index = 0

    def display_current_color(self):
        rgbled(*self.colors[self.current_color_index])

    def seconds_handler(self, alarm):
        self.next_color()
        self.display_current_color()


#############################################################
# Function Name: flash_led
# Description: Will flash the on board RGB LED the specified
# color for a given duration
# Inputs: color=[], time
# Outputs: None
#############################################################
def flash_led(color, time):
    red = 0
    green = 0
    blue = 0
    for i in color:
        if i == 'R':
            red = 128
        elif i == 'G':
            green = 128
        elif i == 'B':
            blue = 128
        else:
            print("Not Valid Color")
            break

    rgbled(red, green, blue)
    sleep(time)
    rgbled(0, 0, 0)
    return


#############################################################
# Function Name: format_rtc
# Description: Creates neat format for date tuple
# Inputs: rtc=()
# Outputs: text
#############################################################
def get_timestamp(rtc=None):
    if rtc is None:
        rtc = machine.RTC().now()

    # for 2nd of February 2017 at 10:30am (TZ 0)
    # rtc.init((2017, 2, 28, 10, 30, 0, 0, 0))
    year = rtc[0]
    month = rtc[1]
    day = rtc[2]
    hour = rtc[3]
    minute = rtc[4]
    second = rtc[5]
    milliseconds = rtc[6]

    date_time = "{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}.{milliseconds:04d}Z".format(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        second=second,
        milliseconds=milliseconds
    )

    return date_time


def get_day_timestamp(rtc=None):
    ts = get_timestamp(rtc)
    return ts.split('T')[0].strip()


def Random():
    r = crypto.getrandbits(32)
    return ((r[0] << 24) + (r[1] << 16) + (r[2] << 8) + r[3]) / 4294967295.0


def get_device_id():
    machine_byte_id = machine.unique_id()
    return hexlify(machine_byte_id).decode()


def configure_uart():
    uart = machine.UART(0, 115200)
    os.dupterm(uart)


def remove_dir(directory, raise_exceptions=False):
    try:
        for filename in os.listdir(directory):
            path = "{}/{}".format(directory, filename)
            remove_dir(path)
        os.remove(directory)
        return True
    except Exception:
        log_message("Failed to remove {}".format(directory))
        if raise_exceptions:
            raise

        return False


def enable_ntp():
    print("Enabling NTP")
    rtc = machine.RTC()
    rtc.ntp_sync('pool.ntp.org')

    while not rtc.synced():
        sleep(1)

    print("NTP Enabled")


def wdt(timeout=600000):
    # Set watchdog timer for 10 minutes
    wdt = machine.WDT(timeout=timeout)
    wdt.feed()


def button_handler(handler, pin="G17"):
    button = machine.Pin(pin, mode=machine.Pin.IN, pull=machine.Pin.PULL_UP)
    button.callback(trigger=machine.Pin.IRQ_LOW_LEVEL, handler=handler)

    return button


def log_message(message):
    timestamp = get_timestamp()
    print("{:28} | {}".format(timestamp, message))


def reset_handler(*args, **kwargs):
    print("Resetting device in 5 seconds")
    sleep(5)
    machine.reset()


def bringup_wlan(ext_ant=False):
    wlan = WLAN()
    wlan.deinit()
    init_kwargs = {"mode": WLAN.STA, "antenna": WLAN.INT_ANT if not ext_ant else WLAN.EXT_ANT}
    wlan.init(**init_kwargs)

    return wlan


def simple_connect(ssid, pw, wlan=None, ext_ant=False, max_attempts=10, log=print):
    if wlan is None:
        wlan = bringup_wlan()

    results = wlan.scan()
    network = None
    for result in results:
        if result.ssid == ssid:
            network = result

    if network is None:
        raise Exception("Network {} not found".format(ssid))

    wlan.connect(ssid, auth=(network.sec, pw))
    for i in range(max_attempts):
        timeouts = 20
        for t in range(timeouts):
            if wlan.isconnected():
                break
            sleep(1)

    log("Connected")
    log(wlan.ifconfig())

    return wlan


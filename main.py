from network import WLAN      # For operation of WiFi network
import time                   # Allows use of time.sleep() for delays
import pycom                  # Base library for Pycom devices
from umqtt import MQTTClient  # For use of MQTT protocol to talk to Adafruit IO
import ubinascii              # Needed to run any MicroPython code
import machine                # Interfaces with hardware components
import micropython            # Needed to run any MicroPython code
import ussl                   # Needed to have TLS/SSL implementation

# BEGIN SETTINGS
# These need to be change to suit your environment
RANDOMS_INTERVAL = 5000 # milliseconds
last_random_sent_ticks = 0  # milliseconds

# Wireless network
WIFI_SSID = "YOUR WIFI NAME"
WIFI_PASS = "YOUR WIFI PASSWORD" # No this is not our regular password. :)

# Adafruit IO (AIO) configuration
AIO_SERVER = "io.adafruit.com"
AIO_USER = "harisahmed"
AIO_PORT = 8883
AIO_KEY = "9c2a405e76f544128b8149ce2f271243"
AIO_CLIENT_ID = ubinascii.hexlify(machine.unique_id())  # Can be anything
AIO_RANDOMS_FEED = "harisahmed/feeds/randoms"

#TLS Parameters
params = {'cert_reqs':ussl.CERT_REQUIRED, 'ca_certs':'/flash/cert/adafruit.cer'}

# END SETTINGS

# RGBLED
# Disable the on-board heartbeat (blue flash every 4 seconds)
# We'll use the LED to respond to messages from Adafruit IO
pycom.heartbeat(False)
time.sleep(0.1) # Workaround for a bug.
                # Above line is not actioned if another
                # process occurs immediately afterwards
pycom.rgbled(0xff0000)  # Status red = not working

# WIFI
# We need to have a connection to WiFi for Internet access
# Code source: https://docs.pycom.io/chapter/tutorials/all/wlan.html

wlan = WLAN(mode=WLAN.STA)
wlan.connect(WIFI_SSID, auth=(WLAN.WPA2, WIFI_PASS), timeout=5000)

while not wlan.isconnected():    # Code waits here until WiFi connects
    machine.idle()

print("Connected to Wifi")
pycom.rgbled(0xffd7000) # Status orange: partially working

# FUNCTIONS

def random_integer(upper_bound):
    return machine.rng() % upper_bound

def send_random():
    global last_random_sent_ticks
    global RANDOMS_INTERVAL

    if ((time.ticks_ms() - last_random_sent_ticks) < RANDOMS_INTERVAL):
        return; # Too soon since last one sent.

    some_number = random_integer(100)
    print("Publishing: {0} to {1} ... ".format(some_number, AIO_RANDOMS_FEED), end='')
    try:
        client.publish(topic=AIO_RANDOMS_FEED, msg=str(some_number))
        print("DONE")
    except Exception as e:
        print("FAILED")
    finally:
        last_random_sent_ticks = time.ticks_ms()

# Use the MQTT protocol to connect to Adafruit IO
client = MQTTClient(AIO_CLIENT_ID, AIO_SERVER, AIO_PORT, AIO_USER, AIO_KEY, ssl=True, ssl_params=params)


client.connect()

print("Connected to %s " % (AIO_SERVER))
pycom.rgbled(0x00ff00) # Status green: online to Adafruit IO

try:                      # Code between try: and finally: may cause an error
                          # so ensure the client disconnects the server if
                          # that happens.
    while 1:              # Repeat this loop forever
        send_random()     # Send a random number to Adafruit IO if it's time.
finally:                  # If an exception is thrown ...
    client.disconnect()   # ... disconnect the client and clean up.
    client = None
    wlan.disconnect()
    wlan = None
    pycom.rgbled(0x000022)# Status blue: stopped
    print("Disconnected from Adafruit IO.")

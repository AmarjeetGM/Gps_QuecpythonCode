from umqtt import MQTTClient
import log
import checkNet
import ujson
import utime
from machine import Pin 
from usr.locator import Locator 
import sms
import ure  
import dataCall

#done signal pin
done_pin = Pin(29, Pin.OUT, Pin.PULL_PU)

# === Project Metadata ===
PROJECT_NAME = "EC200U_MQTT_GPS"
PROJECT_VERSION = "1.0.0"
DEVICE_ID = 98

# === MQTT Configuration ===
MQTT_BROKER = "a1tgjydixa0qkm-ats.iot.us-east-1.amazonaws.com"
MQTT_PORT = 8883
CLIENT_ID = "iotconsole-83e0cb3d-3b1f-46ae-984f-d9cdbc01c2f2"
TOPIC = b"GPS/DATA/3"

# === SSL Certificate Paths ===
CERT_FILE = "/usr/device_cert.pem.crt"
KEY_FILE = "/usr/private_key.pem.key"


# === GPS Locator ===
Loc = Locator()

# === Logging & Network Setup ===
checknet = checkNet.CheckNetwork(PROJECT_NAME, PROJECT_VERSION)
log.basicConfig(level=log.INFO)
mqtt_log = log.getLogger("MQTT")

# === Load Certificates ===
key1, cert1 = None, None
try:
    with open(KEY_FILE, 'r') as f:
        key1 = f.read()
    print("Private key loaded successfully.")
    with open(CERT_FILE, 'r') as f:
        cert1 = f.read()
    print("Device certificate loaded successfully.")
except Exception as e:
    print("Error loading certificates:", str(e))

# === MQTT Message Callback ===
def sub_cb(topic, msg):
    print("Message received: Topic={}, Message={}".format(topic.decode(), msg.decode()))

# === Get UTC Time ===
def get_utc_time():
    utc_time = utime.localtime()
    
    if utc_time is None:
        print("Error: Unable to get UTC time.")
        return "0000-00-00 00:00:00"
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(*utc_time[:6])

# === Get GPS Coordinates with Retry Logic ===
def get_GPS(max_retries=5, delay=5):
    retry_count = 0
    print("Starting GPS acquisition...")
    while retry_count < max_retries:
        print("Attempt to get GPS coordinates...{}".format(retry_count + 1))
        Loc.read_gps()
        print("GPS Read: Lat={}, Long={}".format(Loc.lati, Loc.longi))
        if Loc.lati is not None and Loc.longi is not None:
            print("GPS Acquired: Lat={}, Long={}".format(Loc.lati, Loc.longi))
            return Loc.lati, Loc.longi
        print("GPS not available, retrying...")
        utime.sleep(delay)
        retry_count += 1
    print("Failed to acquire GPS after maximum retries.")
    return None, None


if __name__ == '__main__':
    print("Checking network connection...")
    stagecode, subcode = checknet.wait_network_connected(30)

    if stagecode == 3 and subcode == 1:
        print("Network connection successful!")
        utime.sleep(5)
        initial_msg = "GPS Device {} is ready".format(DEVICE_ID)
        sms.sendTextMsg("8825331697", initial_msg, "GSM")
        try:
            print("Initializing MQTT client...")
            c = MQTTClient(
                client_id=CLIENT_ID,
                server=MQTT_BROKER,
                port=MQTT_PORT,
                ssl=True,
                ssl_params={"key": key1, "cert": cert1},
                keepalive=120
            )
            c.set_callback(sub_cb)

            print("Connecting to AWS IoT Core...")
            c.connect()
            print("Connected to AWS IoT Core!")

            # Attempt GPS fetch with limited retries
            max_attempts =2
            attempt = 0

            while attempt < max_attempts:
                print("Fetching GPS data (Attempt {} of {})...".format(attempt + 1, max_attempts))
                lat, lng = get_GPS()
                print("GPS data fetched: Lat={}, Long={}".format(lat, lng))

                if lat is not None and lng is not None:
                    break  # Exit loop if GPS data is successfully fetched
                else:
                    print("GPS acquisition failed. Retrying after 1 seconds...")
                    utime.sleep(1)
                    attempt += 1

            if lat is not None and lng is not None:
                payload = ujson.dumps({
                    "Device_id": DEVICE_ID,
                    "Latitude": lat,
                    "Longitude": lng,
                    "Timestamp": get_utc_time()
                })

                print("Publishing GPS data:", payload)
                c.publish(TOPIC, payload.encode())
                print("GPS data published successfully!")
                utime.sleep(5)
                initial_msg = "GPS Device {} is in sleep mode".format(DEVICE_ID)
                sms.sendTextMsg("8825331697", initial_msg, "GSM")
                print("Setting up DONE pin...HIGH TO POWERDOWN")
                done_pin.value(1)
            else:
                print("Failed to fetch GPS data after {} attempts. Signaling done.".format(max_attempts))
                sms.sendTextMsg("8825331697", "GPS Device {} failed to fetch after all attempt".format(DEVICE_ID), "GSM")
                done_pin.value(1)  # Signal done after max attempts

        except Exception as e:
            print("Initial connection exception:", str(e))
            done_pin.value(1)  # Signal done on exception

        finally:
            print("Disconnecting MQTT...")
            c.disconnect()
            print("MQTT disconnected successfully!")

    else:
        print("Network connection failed! stagecode=" + str(stagecode) + ", subcode=" + str(subcode))
        sms.sendTextMsg("8825331697", "GPS Device {} failed to connect to network".format(DEVICE_ID), "GSM")
        print("Done pin set to HIGH to indicate failure.")
        done_pin.value(1)  # Signal done if network fails


   


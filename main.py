from umqtt import MQTTClient
import log
import checkNet
import ujson
import utime
from machine import Pin
from usr.locator import Locator

# === Project Metadata ===
PROJECT_NAME = "EC200U_MQTT_GPS"
PROJECT_VERSION = "1.0.0"
DEVICE_ID = 99

# === MQTT Configuration ===
MQTT_BROKER = "a1tgjydixa0qkm-ats.iot.us-east-1.amazonaws.com"
MQTT_PORT = 8883
CLIENT_ID = "iotconsole-83e0cb3d-3b1f-46ae-984f-d9cdbc01c2f2"
TOPIC = b"GPS/DATA"

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
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(*utc_time[:6])

# === Get GPS Coordinates with Retry Logic ===
def get_GPS(max_retries=5, delay=5):
    retry_count = 0
    while retry_count < max_retries:
        print(f"Attempt {retry_count + 1} to get GPS coordinates...")
        Loc.read_gps()
        if Loc.lati is not None and Loc.longi is not None:
            print("GPS Acquired: Lat={}, Long={}".format(Loc.lati, Loc.longi))
            return Loc.lati, Loc.longi
        utime.sleep(delay)
        retry_count += 1
    print("Failed to acquire GPS after maximum retries.")
    return None, None

# === Main ===
if __name__ == '__main__':
    # Define DONE pin (change GPIO4 to your actual connected pin)
    # done_pin = Pin(Pin.GPIO4, Pin.OUT)
    done_pin = Pin(4,Pin.OUT,Pin.PULL_PU)
    done_pin.write(0)  # Start low

    print("Checking network connection...")
    stagecode, subcode = checknet.wait_network_connected(30)

    if stagecode == 3 and subcode == 1:
        print("Network connection successful!")

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

            print("Fetching GPS data...")
            lat, lng = get_GPS()

            if lat is None or lng is None:
                print("GPS data not available, publishing empty coordinates.")
                payload = ujson.dumps({
                    "Device_id": DEVICE_ID,
                    "Latitude": 0,
                    "Longitude": 0,
                    "Timestamp": get_utc_time()
                })
            else:
                payload = ujson.dumps({
                    "Device_id": DEVICE_ID,
                    "Latitude": lat,
                    "Longitude": lng,
                    "Timestamp": get_utc_time()
                })

            print("Publishing GPS data:", payload)
            c.publish(TOPIC, payload.encode())

            utime.sleep(5)

            print("Disconnecting MQTT...")
            c.disconnect()

        except Exception as e:
            print("Exception:", str(e))

    else:
        print("Network connection failed! stagecode=" + str(stagecode) + ", subcode=" + str(subcode))

    # === DONE! Signal Nano Power Timer to cut power ===
    print("Signaling DONE pin HIGH to shut down power...")
    done_pin.write(1)
    utime.sleep(1)
    done_pin.write(0)
    utime.sleep(1)

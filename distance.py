import Jetson.GPIO as GPIO
import time
import firebase_admin
from firebase_admin import credentials, db

# === CONFIGURATION ===

FILE_PATH = 'detection_logs.txt'
TRIG = 35  # Physical pin 35
ECHO = 33  # Physical pin 33

FIREBASE_CREDENTIAL_PATH = 'project8-b295f-firebase-adminsdk-fbsvc-619af81878.json'
FIREBASE_DB_URL = 'https://project8-b295f-default-rtdb.asia-southeast1.firebasedatabase.app/'

# === GPIO SETUP ===

GPIO.setmode(GPIO.BOARD)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# === FIREBASE INITIALIZATION ===

cred = credentials.Certificate(FIREBASE_CREDENTIAL_PATH)
firebase_admin.initialize_app(cred, {
    'databaseURL': FIREBASE_DB_URL
})

# References to Firebase Realtime Database fields
distance_ref = db.reference('distance')
player_ref = db.reference('player')  # <-- Reference to the "player" field

# === FUNCTIONS ===

def read_trigger_file():
    try:
        with open(FILE_PATH, 'r') as file:
            content = file.read().strip().lower()
            return content == 'true'
    except FileNotFoundError:
        return False

def measure_distance():
    GPIO.output(TRIG, False)
    time.sleep(0.1)

    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    timeout_start = time.time() + 1
    while GPIO.input(ECHO) == 0:
        if time.time() > timeout_start:
            print("Timeout: ECHO did not go high")
            return None
    pulse_start = time.time()

    timeout_end = time.time() + 1
    while GPIO.input(ECHO) == 1:
        if time.time() > timeout_end:
            print("Timeout: ECHO did not go low")
            return None
    pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance_cm = round(pulse_duration * 17150, 2)
    distance_m = round(distance_cm / 100, 3)

    return distance_cm, distance_m

# === MAIN LOOP ===

try:
    while True:
        is_player_detected = read_trigger_file()

        # Update player field
        player_ref.set(is_player_detected)

        if is_player_detected:
            result = measure_distance()
            if result is not None:
                distance_cm, distance_m = result
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                print(f"Distance: {distance_cm} cm ({distance_m} m)")

                # Store the data as a structured object in Firebase under "distance"
                distance_ref.set({
                    'cm': distance_cm,
                    'm': distance_m,
                    'timestamp': timestamp
                })

        time.sleep(1)

except KeyboardInterrupt:
    print("\nMeasurement stopped by User")
    GPIO.cleanup()

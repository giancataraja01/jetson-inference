# --- Simple ON/OFF "Blink Test" Code ---
import Jetson.GPIO as GPIO
import time

# Use the same pin as your main script
TWEETER_PIN = 32

print("--- RUNNING HARDWARE DIAGNOSTIC TEST ---")
print("This test will turn the pin ON for 2 seconds, then OFF.")
print("Listen very carefully for a 'click' or 'pop' from the speaker.")

try:
    # Setup GPIO
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(TWEETER_PIN, GPIO.OUT)
    GPIO.output(TWEETER_PIN, GPIO.LOW) # Start with pin OFF
    time.sleep(1)

    # --- Test Starts Now ---
    print("\nTURNING PIN ON... LISTEN NOW!")
    GPIO.output(TWEETER_PIN, GPIO.HIGH) # Turn the pin fully ON
    time.sleep(2) # Keep it on for 2 seconds

    print("TURNING PIN OFF... LISTEN AGAIN.")
    GPIO.output(TWEETER_PIN, GPIO.LOW)  # Turn the pin fully OFF
    time.sleep(1)

    print("\n--- Test Finished ---")

finally:
    GPIO.cleanup()
    print("GPIO resources have been cleaned up.")
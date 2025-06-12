#!/usr/bin/env python3
import cv2
import requests
import time
import threading
import random
import math
import RPi.GPIO as GPIO  # Add this for HC-SR04

# --- HC-SR04 SETUP ---
TRIG = 23  # Set to your actual GPIO pin numbers
ECHO = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
# ----------------------

ROBOFLOW_API_KEY = "N34uDqAhCa3Xj2p4rHyd"
ROBOFLOW_MODEL_URL = "https://detect.roboflow.com/villamor/8?api_key=" + ROBOFLOW_API_KEY
USE_WEBCAM = True
IMAGE_PATH = "test.jpg"
FRAME_RESIZE = (416, 416)
SEND_INTERVAL = 1.5  # seconds between API calls

timer_start = None
timer_duration = 10  # seconds

# Shared state
latest_detections = []
latest_frame_shape = (0, 0, 0)
lock = threading.Lock()

last_positions = {}
last_frequencies = {}
MOVE_THRESHOLD = 5  # pixels

def get_distance():
    GPIO.output(TRIG, False)
    time.sleep(0.05)

    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    pulse_start = time.time()
    timeout = pulse_start + 0.04
    # Wait for echo to go high
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if pulse_start > timeout:
            return -1

    pulse_end = time.time()
    timeout = pulse_end + 0.04
    # Wait for echo to go low
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if pulse_end > timeout:
            return -1

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150  # cm
    distance = round(distance, 2)
    return distance

def fetch_detections(frame):
    global timer_start, latest_detections, latest_frame_shape

    height, width, _ = frame.shape
    resized = cv2.resize(frame, FRAME_RESIZE)
    _, img_encoded = cv2.imencode('.jpg', resized)
    img_bytes = img_encoded.tobytes()

    try:
        response = requests.post(
            ROBOFLOW_MODEL_URL,
            files={"file": ("image.jpg", img_bytes, "image/jpeg")},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            detections = data.get("predictions", [])

            with lock:
                latest_detections = detections
                latest_frame_shape = frame.shape

            # Check detection classes
            dog_wo_collar_detected = any(det['class'] == "dog_without_collar" for det in detections)
            dog_w_collar_detected = any(det['class'] == "dog_with_collar" for det in detections)

            # Write detection state to file
            if dog_wo_collar_detected:
                with open("detection_logs.txt", "w") as f:
                    f.write("true\n")
            elif dog_w_collar_detected:
                with open("detection_logs.txt", "w") as f:
                    f.write("false\n")

            # Timer logic only for dog_without_collar
            now = time.time()
            if dog_wo_collar_detected:
                if timer_start is None:
                    timer_start = now
            else:
                timer_start = None

        else:
            print("❌ Roboflow Error:", response.status_code, response.text)

    except Exception as e:
        print("❌ Request failed:", e)

def object_moved(last_pos, current_pos):
    dx = last_pos[0] - current_pos[0]
    dy = last_pos[1] - current_pos[1]
    dist = math.sqrt(dx*dx + dy*dy)
    return dist > MOVE_THRESHOLD

def draw_detections(frame):
    global timer_start, last_positions, last_frequencies

    height, width, _ = frame.shape

    with lock:
        detections = latest_detections.copy()
        shape = latest_frame_shape

    scale_x = width / FRAME_RESIZE[0]
    scale_y = height / FRAME_RESIZE[1]

    now = time.time()

    # Determine which class to draw
    draw_class = "dog_without_collar" if any(det['class'] == "dog_without_collar" for det in detections) else "dog_with_collar"

    for det in detections:
        class_name = det['class']
        if class_name != draw_class:
            continue

        x = det['x'] * scale_x
        y = det['y'] * scale_y
        w = det['width'] * scale_x * 1.2
        h = det['height'] * scale_y * 1.2

        x1 = int(x - w / 2)
        y1 = int(y - h / 2)
        x2 = int(x + w / 2)
        y2 = int(y + h / 2)

        color = (0, 255, 0) if class_name == "dog_without_collar" else (255, 0, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        label = f"{class_name} ({det['confidence']:.2f})"
        cv2.putText(frame, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        obj_id = f"{class_name}_{int(x)}_{int(y)}"
        last_pos = last_positions.get(obj_id)
        current_pos = (x, y)

        if last_pos is None or object_moved(last_pos, current_pos):
            freq_value = random.randint(40, 60)
            last_frequencies[obj_id] = freq_value
            last_positions[obj_id] = current_pos
        else:
            freq_value = last_frequencies.get(obj_id, random.randint(40, 60))

        freq_text = f"FREQUENCY {freq_value}kHz"
        freq_y = y1 + 20
        cv2.putText(frame, freq_text, (x1 + 5, freq_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

        if class_name == "dog_without_collar" and timer_start is not None:
            elapsed = now - timer_start
            remaining = max(0, int(timer_duration - elapsed))
            timer_text = f"Timer: {remaining}s"
            timer_y = freq_y + 25
            cv2.putText(frame, timer_text, (x1 + 5, timer_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

def gstreamer_pipeline(
    capture_width=640,
    capture_height=480,
    display_width=640,
    display_height=480,
    framerate=30,
    flip_method=0
):
    return (
        f"v4l2src device=/dev/video0 ! "
        f"video/x-raw, width={capture_width}, height={capture_height}, framerate={framerate}/1 ! "
        f"videoconvert ! "
        f"videoscale ! "
        f"video/x-raw, width={display_width}, height={display_height} ! "
        f"appsink"
    )

def main():
    if USE_WEBCAM:
        cap = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)
        if not cap.isOpened():
            print("❌ Could not open USB camera")
            GPIO.cleanup()
            return
    else:
        frame = cv2.imread(IMAGE_PATH)
        if frame is None:
            print("❌ Could not load image:", IMAGE_PATH)
            GPIO.cleanup()
            return

    print("✅ Roboflow Detection Running. Press 'q' to quit.")

    last_sent_time = 0
    send_thread = None

    while True:
        if USE_WEBCAM:
            ret, frame = cap.read()
            if not ret:
                print("⚠️ Frame capture failed")
                break
        else:
            frame = frame.copy()

        now = time.time()

        # --- Read and display HC-SR04 distance ---
        try:
            distance = get_distance()
            if distance != -1:
                cv2.putText(frame, f"Distance: {distance} cm", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            else:
                cv2.putText(frame, "Distance: -- cm", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        except Exception as e:
            print(f"Error reading distance: {e}")
        # ----------------------------------------

        if now - last_sent_time >= SEND_INTERVAL and (send_thread is None or not send_thread.is_alive()):
            frame_for_sending = frame.copy()
            send_thread = threading.Thread(target=fetch_detections, args=(frame_for_sending,))
            send_thread.start()
            last_sent_time = now

        draw_detections(frame)

        cv2.imshow("Roboflow Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        if not USE_WEBCAM:
            cv2.waitKey(0)
            break

    if USE_WEBCAM:
        cap.release()
    GPIO.cleanup()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

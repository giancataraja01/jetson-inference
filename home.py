#!/usr/bin/env python3

import tkinter as tk
from tkinter import font
import subprocess
import Jetson.GPIO as GPIO
import time

# --- Optional Firebase integration ---
import firebase_admin
from firebase_admin import credentials, db

# === CONFIGURATION ===

FILE_PATH = 'detection_logs.txt'
TRIG = 35  # Physical pin 35
ECHO = 33  # Physical pin 33

FIREBASE_CREDENTIAL_PATH = 'project8-b295f-firebase-adminsdk-fbsvc-619af81878.json'
FIREBASE_DB_URL = 'https://project8-b295f-default-rtdb.asia-southeast1.firebasedatabase.app/'

# --- GPIO SETUP ---
GPIO.setmode(GPIO.BOARD)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# --- Firebase Initialization (comment if not needed) ---
cred = credentials.Certificate(FIREBASE_CREDENTIAL_PATH)
firebase_admin.initialize_app(cred, {
    'databaseURL': FIREBASE_DB_URL
})
distance_ref = db.reference('distance')
player_ref = db.reference('player')

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

class ButtonApp:
    def __init__(self, master):
        self.master = master
        master.title("Dog Detection")
        master.geometry("400x450") # Extra space for distance display

        self.camera_process = None
        self.speaker_process = None

        button_font = font.Font(family='Helvetica', size=12, weight='bold')

        main_frame = tk.Frame(master, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_rowconfigure(3, weight=1)
        main_frame.grid_rowconfigure(4, weight=1)

        btn1 = tk.Button(main_frame, text="Start", font=button_font, command=self.action1_clicked)
        btn1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        btn2 = tk.Button(main_frame, text="Test Speaker", font=button_font, command=self.action2_clicked)
        btn2.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        btn3 = tk.Button(main_frame, text="Test Distance", font=button_font, command=self.action3_clicked)
        btn3.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        btn4 = tk.Button(main_frame, text="Test Camera", font=button_font, command=self.action4_clicked)
        btn4.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        btn_stop_camera = tk.Button(main_frame, text="Stop Camera", font=button_font, command=self.stop_camera_clicked, bg="#e08b1c", fg="white")
        btn_stop_camera.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        btn_stop_speaker = tk.Button(main_frame, text="Stop Speaker Test", font=button_font, command=self.stop_speaker_clicked, bg="#1c8be0", fg="white")
        btn_stop_speaker.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        # --- Distance reading label ---
        self.distance_var = tk.StringVar()
        self.distance_var.set("Distance: N/A")
        self.distance_label = tk.Label(main_frame, textvariable=self.distance_var, font=button_font, fg="#1338be")
        self.distance_label.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        quit_button = tk.Button(master, text="Quit", command=self.close_window, bg="#c42b2b", fg="white")
        quit_button.pack(pady=10)

        master.protocol("WM_DELETE_WINDOW", self.close_window)

    def action1_clicked(self):
        print("Button 'Action 1' was clicked!")

    def action2_clicked(self):
        print("Button 'Test Speaker' was clicked!")
        try:
            if self.speaker_process and self.speaker_process.poll() is None:
                self.speaker_process.terminate()
                print("Existing speaker process terminated.")
            self.speaker_process = subprocess.Popen(['aplay', './12000.wav'])
            print("aplay launched.")
        except Exception as e:
            print(f"Failed to launch aplay: {e}")

    def stop_speaker_clicked(self):
        if self.speaker_process and self.speaker_process.poll() is None:
            self.speaker_process.terminate()
            print("Speaker process terminated.")
            self.speaker_process = None
        else:
            print("No speaker process is running.")

    def action3_clicked(self):
        print("Button 'Test Distance' was clicked!")
        try:
            # Directly measure distance instead of launching subprocess
            result = measure_distance()
            if result is not None:
                distance_cm, distance_m = result
                self.distance_var.set(f"Distance: {distance_cm} cm ({distance_m} m)")
                print(f"Distance reading: {distance_cm} cm ({distance_m} m)")
                # --- Optionally update Firebase ---
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                distance_ref.set({
                    'cm': distance_cm,
                    'm': distance_m,
                    'timestamp': timestamp
                })
            else:
                self.distance_var.set("Distance: Error")
                print("Error measuring distance")
        except Exception as e:
            self.distance_var.set("Distance: Error")
            print(f"Exception measuring distance: {e}")

    def action4_clicked(self):
        print("Button 'Test Camera' was clicked!")
        try:
            if self.camera_process and self.camera_process.poll() is None:
                self.camera_process.terminate()
                print("Existing camera process terminated.")
            self.camera_process = subprocess.Popen(['python3', 'my_detection.py'])
            print("my_detection.py launched.")
        except Exception as e:
            print(f"Failed to launch my_detection.py: {e}")

    def stop_camera_clicked(self):
        if self.camera_process and self.camera_process.poll() is None:
            self.camera_process.terminate()
            print("Camera process terminated.")
            self.camera_process = None
        else:
            print("No camera process is running.")

    def close_window(self):
        print("Closing the application...")
        if self.camera_process and self.camera_process.poll() is None:
            self.camera_process.terminate()
            print("Camera process terminated on exit.")
        if self.speaker_process and self.speaker_process.poll() is None:
            self.speaker_process.terminate()
            print("Speaker process terminated on exit.")
        GPIO.cleanup()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ButtonApp(root)
    root.mainloop()

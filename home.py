#!/usr/bin/env python3

import tkinter as tk
from tkinter import font
from tkinter import PhotoImage
import subprocess
import Jetson.GPIO as GPIO
import time
import os

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
        master.geometry("430x530")
        self.camera_process = None
        self.speaker_process = None
        self.distance_monitoring = False
        self.distance_job = None

        button_font = font.Font(family='Helvetica', size=12, weight='bold')

        # Load icons if available
        self.icon_play = self.load_icon('play.png')
        self.icon_stop = self.load_icon('stop.png')
        self.icon_speaker = self.load_icon('speaker.png')
        self.icon_camera = self.load_icon('camera.png')
        self.icon_distance = self.load_icon('distance.png')
        self.icon_monitor = self.load_icon('monitor.png')

        main_frame = tk.Frame(master, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Row 1: Start and Stop (main) ---
        main_row = tk.Frame(main_frame)
        main_row.pack(fill=tk.X, pady=5)
        self.btn_start = tk.Button(main_row, text="Start", font=button_font, command=self.action1_clicked, image=self.icon_play, compound='left', width=130)
        self.btn_start.pack(side=tk.LEFT, padx=(0,8))
        self.btn_stop = tk.Button(main_row, text="Stop", font=button_font, command=self.close_window, image=self.icon_stop, compound='left', bg="#c42b2b", fg="white", width=130)
        self.btn_stop.pack(side=tk.LEFT)

        # --- Row 2: Speaker Test/Stop ---
        speaker_row = tk.Frame(main_frame)
        speaker_row.pack(fill=tk.X, pady=5)
        self.btn_speaker = tk.Button(speaker_row, text="Test Speaker", font=button_font, command=self.action2_clicked, image=self.icon_speaker, compound='left', width=130)
        self.btn_speaker.pack(side=tk.LEFT, padx=(0,8))
        self.btn_speaker_stop = tk.Button(speaker_row, text="Stop Speaker", font=button_font, command=self.stop_speaker_clicked, image=self.icon_stop, compound='left', bg="#1c8be0", fg="white", width=130)
        self.btn_speaker_stop.pack(side=tk.LEFT)

        # --- Row 3: Camera Test/Stop ---
        camera_row = tk.Frame(main_frame)
        camera_row.pack(fill=tk.X, pady=5)
        self.btn_camera = tk.Button(camera_row, text="Test Camera", font=button_font, command=self.action4_clicked, image=self.icon_camera, compound='left', width=130)
        self.btn_camera.pack(side=tk.LEFT, padx=(0,8))
        self.btn_camera_stop = tk.Button(camera_row, text="Stop Camera", font=button_font, command=self.stop_camera_clicked, image=self.icon_stop, compound='left', bg="#e08b1c", fg="white", width=130)
        self.btn_camera_stop.pack(side=tk.LEFT)

        # --- Row 4: Distance Test/Monitor ---
        distance_row = tk.Frame(main_frame)
        distance_row.pack(fill=tk.X, pady=5)
        self.btn_distance = tk.Button(distance_row, text="Test Distance", font=button_font, command=self.action3_clicked, image=self.icon_distance, compound='left', width=120)
        self.btn_distance.pack(side=tk.LEFT, padx=(0,8))
        self.btn_start_monitor = tk.Button(distance_row, text="Start Monitor", font=button_font, command=self.start_distance_monitoring, image=self.icon_monitor, compound='left', bg="#34be13", fg="white", width=120)
        self.btn_start_monitor.pack(side=tk.LEFT, padx=(0,8))
        self.btn_stop_monitor = tk.Button(distance_row, text="Stop Monitor", font=button_font, command=self.stop_distance_monitoring, image=self.icon_stop, compound='left', bg="#be1340", fg="white", width=120)
        self.btn_stop_monitor.pack(side=tk.LEFT)

        # --- Distance display ---
        self.distance_var = tk.StringVar()
        self.distance_var.set("Distance: N/A")
        self.distance_label = tk.Label(main_frame, textvariable=self.distance_var, font=button_font, fg="#1338be")
        self.distance_label.pack(fill=tk.X, pady=(20,5))

        # Quit button at the bottom
        quit_button = tk.Button(master, text="Quit", command=self.close_window, bg="#c42b2b", fg="white")
        quit_button.pack(pady=10)

        master.protocol("WM_DELETE_WINDOW", self.close_window)

    def load_icon(self, filename):
        if os.path.exists(filename):
            try:
                return PhotoImage(file=filename)
            except Exception:
                return None
        else:
            return None

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
            result = measure_distance()
            if result is not None:
                distance_cm, distance_m = result
                self.distance_var.set(f"Distance: {distance_cm} cm ({distance_m} m)")
                print(f"Distance reading: {distance_cm} cm ({distance_m} m)")
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

    # --- Dynamic distance monitoring ---
    def start_distance_monitoring(self):
        if not self.distance_monitoring:
            self.distance_monitoring = True
            self.update_distance()
            print("Distance monitoring started.")

    def stop_distance_monitoring(self):
        self.distance_monitoring = False
        if self.distance_job is not None:
            self.master.after_cancel(self.distance_job)
            self.distance_job = None
        print("Distance monitoring stopped.")

    def update_distance(self):
        if self.distance_monitoring:
            try:
                result = measure_distance()
                if result is not None:
                    distance_cm, distance_m = result
                    self.distance_var.set(f"Distance: {distance_cm} cm ({distance_m} m)")
                    print(f"[Live] Distance: {distance_cm} cm ({distance_m} m)")
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    distance_ref.set({
                        'cm': distance_cm,
                        'm': distance_m,
                        'timestamp': timestamp
                    })
                else:
                    self.distance_var.set("Distance: Error")
            except Exception as e:
                self.distance_var.set("Distance: Error")
                print(f"Exception in live distance: {e}")
            self.distance_job = self.master.after(500, self.update_distance)
        else:
            self.distance_var.set("Distance: N/A")

    def close_window(self):
        print("Closing the application...")
        self.stop_distance_monitoring()
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

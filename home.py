#!/usr/bin/env python3

import tkinter as tk
from tkinter import font
from tkinter import ttk
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

def kill_all_aplay():
    try:
        os.system("pkill -9 aplay")
        print("All aplay processes killed.")
    except Exception as e:
        print(f"Error killing aplay processes: {e}")

class ButtonApp:
    def __init__(self, master):
        self.master = master
        master.title("Dog Detection")
        master.geometry("500x500")

        self.camera_process = None
        self.speaker_process = None
        self.distance_monitoring = False
        self.distance_job = None

        button_font = font.Font(family='Helvetica', size=12, weight='bold')

        main_frame = tk.Frame(master, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_columnconfigure(2, weight=1)
        for i in range(6):
            main_frame.grid_rowconfigure(i, weight=1)

        # Start Detection button
        btn1 = tk.Button(main_frame, text="Start Detection", font=button_font, command=self.start_camera_clicked)
        btn1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Speaker dropdown
        self.speaker_files = [
            'Select Frequency',
            '12000.wav', '15000.wav', '20000.wav', '40000.wav', '50000.wav', '60000.wav'
        ]
        self.speaker_var = tk.StringVar()
        self.speaker_var.set('Select Frequency')
        self.speaker_dropdown = ttk.Combobox(
            main_frame, textvariable=self.speaker_var, values=self.speaker_files, font=button_font, state='readonly'
        )
        self.speaker_dropdown.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.speaker_dropdown.bind("<<ComboboxSelected>>", self.on_speaker_selected)

        # Stop Detection button
        btn_stop_detection = tk.Button(
            main_frame, text="Stop Detection", font=button_font,
            command=self.stop_detection_clicked, bg="#be1313", fg="white"
        )
        btn_stop_detection.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

        btn3 = tk.Button(main_frame, text="Test Distance", font=button_font, command=self.action3_clicked)
        btn3.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        btn4 = tk.Button(main_frame, text="Test Camera", font=button_font, command=self.action4_clicked)
        btn4.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        btn_stop_camera = tk.Button(main_frame, text="Stop Camera", font=button_font, command=self.stop_camera_clicked, bg="#e08b1c", fg="white")
        btn_stop_camera.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        btn_stop_speaker = tk.Button(main_frame, text="Stop Speaker Test", font=button_font, command=self.stop_speaker_clicked, bg="#1c8be0", fg="white")
        btn_stop_speaker.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        # Distance label
        self.distance_var = tk.StringVar()
        self.distance_var.set("Distance: N/A")
        self.distance_label = tk.Label(main_frame, textvariable=self.distance_var, font=button_font, fg="#1338be")
        self.distance_label.grid(row=4, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

        # Start/Stop Monitor
        self.btn_start_monitor = tk.Button(
            main_frame, text="Start Monitor", font=button_font,
            command=self.start_distance_monitoring, bg="#34be13", fg="white"
        )
        self.btn_start_monitor.grid(row=5, column=0, sticky="nsew", padx=5, pady=5)

        self.btn_stop_monitor = tk.Button(
            main_frame, text="Stop Monitor", font=button_font,
            command=self.stop_distance_monitoring, bg="#be1340", fg="white"
        )
        self.btn_stop_monitor.grid(row=5, column=1, sticky="nsew", padx=5, pady=5)

        quit_button = tk.Button(master, text="Quit", command=self.close_window, bg="#c42b2b", fg="white")
        quit_button.pack(pady=10)

        master.protocol("WM_DELETE_WINDOW", self.close_window)

    def on_speaker_selected(self, event):
        selected_file = self.speaker_var.get()
        if selected_file != 'Select Frequency':
            self.play_speaker_selected(selected_file)

    def play_speaker_selected(self, selected_file):
        print(f"Playing sound: {selected_file}")
        try:
            # Stop any existing speaker process
            kill_all_aplay()
            self.speaker_process = subprocess.Popen(['aplay', f'./{selected_file}'])
            print("aplay launched.")
        except Exception as e:
            print(f"Failed to launch aplay: {e}")

    def stop_speaker_clicked(self):
        kill_all_aplay()
        self.speaker_process = None
        self.speaker_var.set('Select Frequency')
        print("All aplay processes killed (Stop Speaker Test).")

    def start_camera_clicked(self):
        print("Start button pressed! Starting camera...")
        try:
            if self.camera_process and self.camera_process.poll() is None:
                self.camera_process.terminate()
                try:
                    self.camera_process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self.camera_process.kill()
                print("Existing camera process terminated.")
                self.camera_process = None
            self.camera_process = subprocess.Popen(['python3', 'my_detection.py'])
            print("Camera started.")
            self.start_distance_monitoring()  # <-- Start Distance Monitoring automatically!
        except Exception as e:
            print(f"Failed to start camera: {e}")

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
                try:
                    self.camera_process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self.camera_process.kill()
                print("Existing camera process terminated.")
                self.camera_process = None
            self.camera_process = subprocess.Popen(['python3', 'testcamera.py'])
            print("testcamera.py launched.")
        except Exception as e:
            print(f"Failed to launch testcamera.py: {e}")

    def stop_camera_clicked(self):
        if self.camera_process and self.camera_process.poll() is None:
            self.camera_process.terminate()
            try:
                self.camera_process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.camera_process.kill()
            print("Camera process terminated.")
            self.camera_process = None
        else:
            print("No camera process is running.")

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

    def stop_detection_clicked(self):
        # Stop camera process
        if self.camera_process and self.camera_process.poll() is None:
            self.camera_process.terminate()
            try:
                self.camera_process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.camera_process.kill()
            print("Camera process terminated by Stop Detection.")
            self.camera_process = None

        # Stop speaker process (audio)
        kill_all_aplay()
        self.speaker_process = None
        self.speaker_var.set('Select Frequency')
        print("All aplay processes killed (Stop Detection).")

        self.stop_distance_monitoring()
        print("All detection processes stopped.")

    def close_window(self):
        print("Closing the application...")
        self.stop_distance_monitoring()
        if self.camera_process and self.camera_process.poll() is None:
            self.camera_process.terminate()
            try:
                self.camera_process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.camera_process.kill()
            print("Camera process terminated on exit.")
        kill_all_aplay()
        self.speaker_process = None
        print("All aplay processes killed on exit.")
        GPIO.cleanup()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ButtonApp(root)
    root.mainloop()

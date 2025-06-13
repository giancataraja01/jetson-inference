#!/usr/bin/env python3

import tkinter as tk
from tkinter import font
from tkinter import ttk, messagebox
import subprocess
import Jetson.GPIO as GPIO
import os

# === CONFIGURATION ===
TRIG = 35  # Physical pin 35
ECHO = 33  # Physical pin 33

# --- GPIO SETUP ---
GPIO.setmode(GPIO.BOARD)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

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
        master.geometry("340x230")

        self.camera_process = None

        button_font = font.Font(family='Helvetica', size=12, weight='bold')

        main_frame = tk.Frame(master, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # --- DROPDOWN FOR FREQUENCY SELECTION ---
        self.freq_var = tk.StringVar(value="Select Frequency")
        self.freq_options = ["Select Frequency"] + [f"{khz}khz" for khz in range(10, 61)]
        freq_label = tk.Label(main_frame, text="Select Frequency:")
        freq_label.grid(row=0, column=0, columnspan=2, pady=(0,5))
        self.freq_dropdown = ttk.Combobox(main_frame, textvariable=self.freq_var, values=self.freq_options, state="readonly")
        self.freq_dropdown.grid(row=1, column=0, columnspan=2, pady=(0, 10), sticky="ew")

        # Start Detection button
        btn_start = tk.Button(main_frame, text="Start Detection", font=button_font, command=self.start_camera_clicked)
        btn_start.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        # Stop Detection button
        btn_stop = tk.Button(main_frame, text="Stop Detection", font=button_font,
                             command=self.stop_detection_clicked, bg="#be1313", fg="white")
        btn_stop.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)

        quit_button = tk.Button(master, text="Quit", command=self.close_window, bg="#c42b2b", fg="white")
        quit_button.pack(pady=10)

        master.protocol("WM_DELETE_WINDOW", self.close_window)

    def start_camera_clicked(self):
        selected_freq = self.freq_var.get()
        print(f"Start button pressed! Selected frequency: {selected_freq}")

        if selected_freq == "Select Frequency":
            messagebox.showwarning("Selection Required", "Please select a frequency before starting detection.")
            return

        try:
            if self.camera_process and self.camera_process.poll() is None:
                self.camera_process.terminate()
                try:
                    self.camera_process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self.camera_process.kill()
                print("Existing camera process terminated.")
                self.camera_process = None

            khz = selected_freq.replace("khz", "")
            script_to_run = f"my_detection{khz}khz.py"

            if selected_freq == "60khz":
                print("Running detection for 60khz - will check for 'dog_without_collar' before executing.")
                result = subprocess.run(['python3', script_to_run], capture_output=True, text=True)
                if "dog_without_collar" in result.stdout:
                    print("'dog_without_collar' detected. Executing my_detection60khz.py.")
                    self.camera_process = subprocess.Popen(['python3', script_to_run])
                else:
                    print("'dog_without_collar' not detected. Not executing my_detection60khz.py.")
            else:
                print(f"Executing {script_to_run} for {selected_freq}.")
                self.camera_process = subprocess.Popen(['python3', script_to_run])

            print("Camera started.")
        except Exception as e:
            print(f"Failed to start camera: {e}")

    def stop_detection_clicked(self):
        if self.camera_process and self.camera_process.poll() is None:
            self.camera_process.terminate()
            try:
                self.camera_process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.camera_process.kill()
            print("Camera process terminated by Stop Detection.")
            self.camera_process = None

        kill_all_aplay()
        print("All aplay processes killed (Stop Detection).")

    def close_window(self):
        print("Closing the application...")
        if self.camera_process and self.camera_process.poll() is None:
            self.camera_process.terminate()
            try:
                self.camera_process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.camera_process.kill()
            print("Camera process terminated on exit.")
        kill_all_aplay()
        print("All aplay processes killed on exit.")
        GPIO.cleanup()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ButtonApp(root)
    root.mainloop()

#!/usr/bin/env python3

import tkinter as tk
from tkinter import font
import subprocess

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
            result = subprocess.run(['python3', 'distance.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            if result.returncode == 0:
                output = result.stdout.strip()
                self.distance_var.set(f"Distance: {output}")
                print(f"Distance reading: {output}")
            else:
                self.distance_var.set("Distance: Error")
                print(f"Error in distance.py: {result.stderr.strip()}")
        except Exception as e:
            self.distance_var.set("Distance: Error")
            print(f"Exception running distance.py: {e}")

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
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ButtonApp(root)
    root.mainloop()

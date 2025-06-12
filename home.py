#!/usr/bin/env python3

import tkinter as tk
from tkinter import font
import subprocess

class ButtonApp:
    def __init__(self, master):
        """
        Initializes the application window.
        'master' is the main window (the root).
        """
        self.master = master
        master.title("Dog Detection")
        master.geometry("400x350") # Increased height for extra button

        # --- Track the camera process ---
        self.camera_process = None

        # --- Configure a custom font for the buttons ---
        button_font = font.Font(family='Helvetica', size=12, weight='bold')

        # --- Create a main frame to hold all the widgets ---
        main_frame = tk.Frame(master, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Configure grid for 3 rows x 2 columns ---
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)

        # Button 1
        btn1 = tk.Button(main_frame, text="Start", font=button_font, command=self.action1_clicked)
        btn1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Button 2 - Test Speaker
        btn2 = tk.Button(main_frame, text="Test Speaker", font=button_font, command=self.action2_clicked)
        btn2.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Button 3
        btn3 = tk.Button(main_frame, text="Test Distance", font=button_font, command=self.action3_clicked)
        btn3.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Button 4
        btn4 = tk.Button(main_frame, text="Test Camera", font=button_font, command=self.action4_clicked)
        btn4.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        # --- Stop Camera Button ---
        btn_stop = tk.Button(main_frame, text="Stop Camera", font=button_font, command=self.stop_camera_clicked, bg="#e08b1c", fg="white")
        btn_stop.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        # --- Create a Quit button ---
        quit_button = tk.Button(master, text="Quit", command=self.close_window, bg="#c42b2b", fg="white")
        quit_button.pack(pady=10)

        # --- Handle window close event (clicking the 'X' button) ---
        master.protocol("WM_DELETE_WINDOW", self.close_window)

    def action1_clicked(self):
        """Placeholder function for Button 1."""
        print("Button 'Action 1' was clicked!")

    def action2_clicked(self):
        """Executes playwav.py when 'Test Speaker' is clicked."""
        print("Button 'Test Speaker' was clicked!")
        try:
            subprocess.Popen(['python3', 'playwav.py'])
            print("playwav.py launched.")
        except Exception as e:
            print(f"Failed to launch playwav.py: {e}")

    def action3_clicked(self):
        """Placeholder function for Button 3."""
        print("Button 'Action 3' was clicked!")

    def action4_clicked(self):
        """Executes my_detection.py when 'Test Camera' is clicked."""
        print("Button 'Test Camera' was clicked!")
        try:
            # If a camera process is already running, terminate it first
            if self.camera_process and self.camera_process.poll() is None:
                self.camera_process.terminate()
                print("Existing camera process terminated.")
            self.camera_process = subprocess.Popen(['python3', 'my_detection.py'])
            print("my_detection.py launched.")
        except Exception as e:
            print(f"Failed to launch my_detection.py: {e}")

    def stop_camera_clicked(self):
        """Stops the camera process if running."""
        if self.camera_process and self.camera_process.poll() is None:
            self.camera_process.terminate()
            print("Camera process terminated.")
            self.camera_process = None
        else:
            print("No camera process is running.")

    def close_window(self):
        """Closes the application."""
        print("Closing the application...")
        # Ensure camera process is terminated on exit
        if self.camera_process and self.camera_process.poll() is None:
            self.camera_process.terminate()
            print("Camera process terminated on exit.")
        self.master.destroy()

# --- Main execution block ---
if __name__ == "__main__":
    # Create the main window
    root = tk.Tk()
    
    # Create an instance of our app class
    app = ButtonApp(root)
    
    # Start the GUI event loop
    root.mainloop()

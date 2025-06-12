#!/usr/bin/env python3

import tkinter as tk
from tkinter import font

class ButtonApp:
    def __init__(self, master):
        """
        Initializes the application window.
        'master' is the main window (the root).
        """
        self.master = master
        master.title("Simple UI for Jetson Nano")
        master.geometry("400x300") # Set window size: width x height

        # --- Configure a custom font for the buttons ---
        button_font = font.Font(family='Helvetica', size=12, weight='bold')

        # --- Create a main frame to hold all the widgets ---
        # Using padding to give some space around the edges
        main_frame = tk.Frame(master, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Create the four main buttons ---
        # We will arrange them in a 2x2 grid within the frame
        # .grid() is great for organizing widgets in rows and columns
        
        # Configure the grid columns to have equal weight, so they expand equally
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        # Configure grid rows to have equal weight
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # Button 1
        btn1 = tk.Button(main_frame, text="Action 1", font=button_font, command=self.action1_clicked)
        btn1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Button 2
        btn2 = tk.Button(main_frame, text="Action 2", font=button_font, command=self.action2_clicked)
        btn2.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Button 3
        btn3 = tk.Button(main_frame, text="Action 3", font=button_font, command=self.action3_clicked)
        btn3.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Button 4
        btn4 = tk.Button(main_frame, text="Action 4", font=button_font, command=self.action4_clicked)
        btn4.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        # --- Create a Quit button ---
        quit_button = tk.Button(master, text="Quit", command=self.close_window, bg="#c42b2b", fg="white")
        quit_button.pack(pady=10)

        # --- Handle window close event (clicking the 'X' button) ---
        master.protocol("WM_DELETE_WINDOW", self.close_window)

    def action1_clicked(self):
        """Placeholder function for Button 1."""
        print("Button 'Action 1' was clicked!")

    def action2_clicked(self):
        """Placeholder function for Button 2."""
        print("Button 'Action 2' was clicked!")

    def action3_clicked(self):
        """Placeholder function for Button 3."""
        print("Button 'Action 3' was clicked!")

    def action4_clicked(self):
        """Placeholder function for Button 4."""
        print("Button 'Action 4' was clicked!")
        
    def close_window(self):
        """Closes the application."""
        print("Closing the application...")
        self.master.destroy()

# --- Main execution block ---
if __name__ == "__main__":
    # Create the main window
    root = tk.Tk()
    
    # Create an instance of our app class
    app = ButtonApp(root)
    
    # Start the GUI event loop
    root.mainloop()
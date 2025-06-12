import subprocess
import os

# --- Configuration ---
# The path to your sound file.
# The './' means it's in the same directory as the script.
WAV_FILE_PATH = './12000.wav' 
# ---------------------

# Check if the file actually exists before trying to play it
if not os.path.exists(WAV_FILE_PATH):
    print(f"Error: The file '{WAV_FILE_PATH}' was not found.")
    print("Please make sure your .wav file is in the same directory as this script.")
else:
    try:
        print(f"Playing '{WAV_FILE_PATH}'...")
        # Use subprocess to call the 'aplay' command-line tool.
        # This is the standard audio player for the ALSA sound system on Linux.
        subprocess.run(['aplay', WAV_FILE_PATH], check=True)
        print("Playback finished.")

    except subprocess.CalledProcessError as e:
        print(f"Error during playback: {e}")
        print("Is your speaker plugged into a USB audio adapter?")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

import mss
import numpy as np
import serial
import time
import threading
import pystray
import os
import sys
import json
from PIL import Image

# --- Default Configuration ---
# Used if config.json is missing or corrupt
DEFAULT_CONFIG = {
    "com_port": "COM3",          
    "baud_rate": 115200, 
    "num_leds": 60, 
    "monitor_index": 1, 
    "gamma": 2.2,
    "depth": 100,
    "leds_per_side": {
        "left": 10,
        "top": 20,
        "right": 10,
        "bottom": 20
    }
}

# --- Global State ---
is_running = True
should_exit = False
gamma_table = None  # Calculated dynamically based on config

# --- Helper Functions ---

def resource_path(relative_path):
    """ Get absolute path to resource. Works for dev and for PyInstaller .exe """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_config():
    """ Load config.json or create default if missing """
    config_filename = "config.json"
    
    # Determine correct path for config file (executable dir vs script dir)
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    full_config_path = os.path.join(application_path, config_filename)

    # Create file if it doesn't exist
    if not os.path.exists(full_config_path):
        print(f"Config not found. Creating default at: {full_config_path}")
        try:
            with open(full_config_path, "w") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
        except Exception as e:
            print(f"Error creating config: {e}")
            return DEFAULT_CONFIG

    # Load file
    try:
        with open(full_config_path, "r") as f:
            user_config = json.load(f)
            # Merge with default to ensure all keys exist
            final_config = DEFAULT_CONFIG.copy()
            final_config.update(user_config)
            print(f"Loaded config from {full_config_path}")
            return final_config
    except Exception as e:
        print(f"Error reading config ({e}). Using defaults.")
        return DEFAULT_CONFIG

# --- Image Processing ---

def process_side(raw_image, num_leds, reverse=False):
    """ Resize screen section to calculate average color per LED """
    img = Image.fromarray(raw_image)
    
    # Resize to (num_leds x 1) averages the pixels automatically
    resized_img = img.resize((num_leds, 1), Image.Resampling.BILINEAR)
    color_data = np.array(resized_img)[0]
    
    # Apply gamma correction using the pre-calculated table
    corrected_color = gamma_table[color_data]
    
    if reverse:
        corrected_color = corrected_color[::-1]
        
    return corrected_color.flatten().tobytes()

def send_black_screen(ser, num_leds):
    """ Send a full black frame to turn off LEDs """
    try:
        black_data = b'\x00' * (num_leds * 3)
        count = num_leds * 3 - 1
        checksum = (count >> 8) ^ (count & 0xff) ^ 0x55
        packet = b'Ada' + bytes([count >> 8, count & 0xff, checksum]) + black_data
        ser.write(packet)
        time.sleep(0.0015)
    except Exception as e:
        print(f"Failed to send black screen: {e}")

# --- Main Logic (Worker Thread) ---

def ambilight_logic():
    global gamma_table
    print(f"[Thread] Ambilight Worker Started")

    # 1. Load Configuration
    conf = load_config()
    
    # 2. Extract variables
    com = conf["com_port"]
    baud = conf["baud_rate"]
    total_leds = conf["num_leds"]
    monitor_idx = conf["monitor_index"]
    depth = conf["depth"]
    
    # Calculate Gamma Table based on config
    gamma_val = conf["gamma"]
    gamma_table = np.array([int((i / 255.0) ** gamma_val * 255) for i in range(256)]).astype(np.uint8)

    # Extract LED counts per side
    leds_l = conf["leds_per_side"]["left"]
    leds_t = conf["leds_per_side"]["top"]
    leds_r = conf["leds_per_side"]["right"]
    leds_b = conf["leds_per_side"]["bottom"]

    try:
        ser = serial.Serial(com, baud, timeout=1)
        time.sleep(2)
        print(f"[Thread] Connected to {com} @ {baud}! Streaming...")

        with mss.mss() as sct:
            # Safety check for monitor index
            if monitor_idx >= len(sct.monitors):
                print(f"Error: Monitor {monitor_idx} not found. Using primary (1).")
                monitor_idx = 1
                
            monitor = sct.monitors[monitor_idx]
            lights_are_off_physically = False 

            while not should_exit:
                if is_running:
                    lights_are_off_physically = False 
                    ser.reset_input_buffer()

                    # Capture Screen
                    sct_img = sct.grab(monitor)
                    img = np.array(sct_img)[:, :, :3]
                    img = img[:, :, ::-1] # Convert BGR to RGB
                    
                    h, w, _ = img.shape
                    
                    # Define capture depth based on config
                    safe_depth_x = min(depth, w // 2)
                    safe_depth_y = min(depth, h // 2)
                    
                    # Crop the 4 sides
                    img_left = img[:, :safe_depth_x]      
                    img_top = img[:safe_depth_y, :]
                    img_right = img[:, -safe_depth_x:]  
                    img_bottom = img[-safe_depth_y:, :]
                    
                    # Process each side (Transpose vertical sides)
                    color_left = process_side(img_left.transpose(1, 0, 2), leds_l, True)
                    color_top = process_side(img_top, leds_t, False)
                    color_right = process_side(img_right.transpose(1, 0, 2), leds_r, False)
                    color_bottom = process_side(img_bottom, leds_b, True)

                    color_data = color_left + color_top + color_right + color_bottom
                                
                    # Construct Adalight Packet with Checksum
                    count = total_leds * 3 - 1
                    checksum = (count >> 8) ^ (count & 0xff) ^ 0x55
                    packet = b'Ada' + \
                        bytes([count >> 8, count & 0xff, checksum]) + \
                        color_data

                    ser.write(packet)
                    time.sleep(0.0015)
                
                else:
                    # Paused state (User toggled off)
                    if not lights_are_off_physically:
                        print("[Thread] Turning LEDs off...")
                        send_black_screen(ser, total_leds)
                        lights_are_off_physically = True 
                    
                    # Save CPU when idle
                    time.sleep(0.5)

            # --- Exit Cleanup ---
            print("[Thread] Exiting...")
            send_black_screen(ser, total_leds)
            ser.close()

    except Exception as e:
        print(f'[Error] Logic crashed: {e}')
    
# --- GUI / System Tray ---

def on_clicked(icon, item):
    global is_running, should_exit

    if str(item) == "Toggle On/Off":
        is_running = not is_running
        status = "ON" if is_running else "OFF"
        print(f"[GUI] Lights are now: {status}")

    elif str(item) == "Exit":
        should_exit = True
        icon.stop()

def main():
    # Load icon safely
    image_path = resource_path("icon.png")
    try:
        image = Image.open(image_path)
    except Exception as e:
        print(f"[Warning] Icon error ({e}). Using fallback.")
        image = Image.new('RGB', (64, 64), color='red')

    # Start Worker Thread
    led_thread = threading.Thread(target=ambilight_logic)
    led_thread.daemon = True
    led_thread.start()

    # Start System Tray Icon
    icon = pystray.Icon("Ambilight", image, menu=pystray.Menu(
        pystray.MenuItem("Toggle On/Off", on_clicked),
        pystray.MenuItem("Exit", on_clicked)
    ))
    
    print("[Main] System Tray Icon started...")
    icon.run()

if __name__ == '__main__':
    main()

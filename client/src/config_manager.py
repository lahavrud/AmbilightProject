import json
import os 
import requests 
import sys

class ConfigManager:
    def __init__(self):
        self.default_config = {
            "com_port": "COM3",
            "baud_rate": 115200,
            "esp_ip": "ambilight.local",
            "num_leds": 60,
            "monitor_index": 1,
            "gamma": 2.2,
            "leds_per_side": {
                "left": 10, "top": 20, "right": 10, "bottom": 20
            }
        }
        self.config = self.default_config.copy()
    
    def get_local_path(self):
        """Finds the correct path for config.json (works in Dev and Exe)"""
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            base_path = os.path.dirname(base_path)
        return os.path.join(base_path, 'config.json')
    
    def load_local_config(self):
        """Loads bootstrap settings (COM port, IP) from local file"""
        path = self.get_local_path()

        if not os.path.exists(path):
            print(f"[Config] File not found at {path}, creating defaults.")
            self._save_local_config(self.default_config)
            return

        try:
            with open(path, 'r') as f:
                local_data = json.load(f)
                self.config.update(local_data)
                print(f"[Config] Loaded local settings from {path}")
        except Exception as e:
            print(f"[Config] Error loading local file: {e}")

    def sync_with_esp(self):
        """Fetches config settings from ESP32"""
        ip = self.config.get("esp_ip", "ambilight.local")
        url = f"http://{ip}/config"

        print(f"[Config] Connecting to ESP at {url}...")

        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                remote_data = response.json()

                self.config.update(remote_data)

                print("[Config] Successfully synced with ESP32!")
                print(f"Leds: {self.config['num_leds']}, Brightness: {self.config['brightness']}")
            else:
                print(f"[Config] ESP returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[Config] Failed to connect to ESP: {e}")
            print("Using local/default values instead.")
    def get(self, key):
        return self.config.get(key)
import json
import os
import requests
import sys
import copy


class ConfigManager:
    def __init__(self):
        self.default_config = {
            "network": {"hostname": "ambilight", "wifi_ssid": "", "wifi_pass": ""},
            "hardware": {
                "baud_rate": 115200,
                "num_leds": 60,
                "brightness": 50,
                "max_milliamps": 1500,
                "smoothing_speed": 20,
            },
            "client": {
                "com_port": "COM3",
                "monitor_index": 1,
                "gamma": 2.2,
                "depth": 100,
                "layout": {"left": 10, "top": 20, "right": 10, "bottom": 20},
            },
        }
        self.config = copy.deepcopy(self.default_config)

    def get_local_path(self):
        """Finds the correct path for config.json (Works for Dev and Exe)"""
        if getattr(sys, "frozen", False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            base_path = os.path.dirname(base_path)  # Go up one level from src
        return os.path.join(base_path, "config.json")

    def _save_local_config(self, data):
        """Saves the current config to config.json"""
        try:
            path = self.get_local_path()
            with open(path, "w") as f:
                json.dump(data, f, indent=4)
            print(f"[Config] Saved settings to {path}")
        except Exception as e:
            print(f"[Config] Could not save config: {e}")

    def load_local_config(self):
        """Loads settings from local file, creates default if missing"""
        path = self.get_local_path()

        if not os.path.exists(path):
            print(f"[Config] File not found at {path}, creating defaults.")
            self._save_local_config(self.config)
            return

        try:
            with open(path, "r") as f:
                local_data = json.load(f)

                for section in ["network", "hardware", "client"]:
                    if section in local_data:
                        self.config.setdefault(section, {}).update(local_data[section])

                print(f"[Config] Loaded local settings from {path}")
        except Exception as e:
            print(f"[Config] Error loading local file: {e}")
            print("[Config] Using defaults.")

    def sync_with_esp(self):
        """Fetches config settings from ESP32 and updates local config"""
        hostname = self.get_nested("network", "hostname") or "ambilight.local"

        if not hostname.endswith(".local") and "." not in hostname:
            address = f"{hostname}.local"
        else:
            address = hostname

        url = f"http://{address}/config"
        print(f"[Config] Connecting to ESP at {url}...")

        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                remote_data = response.json()
                print(f"[DEBUG] Received from ESP: {remote_data}")

                if "hardware" in remote_data:
                    self.config["hardware"].update(remote_data["hardware"])

                if "client" in remote_data:
                    self.config["client"].update(remote_data["client"])

                if "network" in remote_data:
                    if "hostname" in remote_data["network"]:
                        self.config["network"]["hostname"] = remote_data["network"][
                            "hostname"
                        ]
                    if "wifi_ssid" in remote_data["network"]:
                        self.config["network"]["wifi_ssid"] = remote_data["network"][
                            "wifi_ssid"
                        ]

                self._save_local_config(self.config)
                print("[Config] Successfully synced with ESP32 and saved!")
            else:
                print(f"[Config] ESP returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[Config] Failed to connect to ESP: {e}")
            print("         Using local values.")

    def get_nested(self, section, key, default=None):
        """
        Safe way to access nested config values.
        Usage: cfg.get_nested("client", "com_port")
        """
        section_data = self.config.get(section, {})
        if isinstance(section_data, dict):
            return section_data.get(key, default)
        return default

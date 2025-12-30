import threading
import time
from src.config_manager import ConfigManager
from src.screen_grabber import ScreenGrabber
from src.channels.serial_channel import SerialChannel
from src.channels.udp_channel import UdpChannel
from src.system_tray import SystemTray
from src.models import AppMode


class AmbilightApp:
    """
    Main Application Controller (State Machine Version).
    """

    def __init__(self):
        # --- Component Initialization ---
        print("[Main] Initializing ConfigManager...")
        self.config_mgr = ConfigManager()
        self.config_mgr.load_local_config()

        # --- Transmitter Factory Logic ---
        conn_type = str(
            self.config_mgr.get_nested("client", "connection_type", "serial")
        )

        if conn_type == "udp":
            host = str(
                self.config_mgr.get_nested("network", "hostname") or "ambilight.local"
            )
            udp_port = int(self.config_mgr.get_nested("network", "udp_port") or 8888)

            print(f"[Main] Initializing UDP Transmitter ({host}:{udp_port})...")
            self.esp_link = UdpChannel(host, udp_port)

        else:
            # Fallback to Serial
            com_port = str(self.config_mgr.get_nested("client", "com_port") or "COM3")
            baud = int(self.config_mgr.get_nested("hardware", "baud_rate") or 115200)

            print(f"[Main] Initializing Serial Transmitter ({com_port})...")
            self.esp_link = SerialChannel(port=com_port, baud_rate=baud)

        # --- Sync Hardware Logic (Startup) ---
        self.pull_hardware_config()

        print("[Main] Initializing Screen Grabber...")
        self.grabber = ScreenGrabber(self.config_mgr)

        # --- State Management ---
        self.current_mode = AppMode.OFF  # The Single Source of Truth
        self.should_exit = False
        self._observers = []  # List of GUI listeners

        self.led_thread = None
        self.tray_thread = None
        self.tray = None

    # ==========================================
    #            Observer Pattern
    # ==========================================

    def register_observer(self, callback_func):
        """GUI/Tray register here to get updates when mode changes"""
        self._observers.append(callback_func)

    def _notify_observers(self):
        """Notify all listeners that state has changed"""
        for callback in self._observers:
            try:
                callback(self.current_mode)
            except Exception as e:
                print(f"[Observer Error] {e}")

    # ==========================================
    #            Thread Management
    # ==========================================

    def start_worker_thread(self):
        if self.led_thread is None or not self.led_thread.is_alive():
            self.led_thread = threading.Thread(target=self.worker_logic)
            self.led_thread.daemon = True
            self.led_thread.start()
            print("[Main] Worker (LEDs) thread started.")

    def start_tray_thread(self):
        self.tray = SystemTray(self)
        self.tray_thread = threading.Thread(target=self.tray.run)
        self.tray_thread.daemon = True
        self.tray_thread.start()
        print("[Main] System Tray thread started.")

    def stop_all(self):
        print("[Main] Stopping all threads...")
        self.should_exit = True
        if self.tray:
            self.tray.stop()

    # ==========================================
    #            Core Logic (State Aware)
    # ==========================================

    def worker_logic(self):
        print("[Worker] Logic loop started.")

        total_leds = int(self.config_mgr.get_nested("hardware", "num_leds") or 60)
        black_frame = b"\x00" * (total_leds * 3)
        lights_physically_off = False

        while not self.should_exit:
            if self.current_mode == AppMode.AMBILIGHT:
                frame = self.grabber.get_frame_bytes()
                if frame:
                    self.esp_link.send_colors(frame)
                    lights_physically_off = False

            else:
                # In any other mode (OFF, RAINBOW, STATIC), PC stops sending data
                if not lights_physically_off:
                    self.esp_link.send_colors(black_frame)
                    lights_physically_off = True

                time.sleep(0.5)

        self.esp_link.send_colors(black_frame)
        self.esp_link.disconnect()
        print("[Worker] Logic loop finished.")

    # ==========================================
    #            Calibration
    # ==========================================
    def update_setting(self, key, value):
        """
        Updates a setting dynamically and reloads necessary components.
        Handles cropping, depth, monitor index, and gamma.
        """
        needs_grabber_reload = False
        needs_esp_sync = False

        # --- CLIENT ---
        if key == "gamma":
            self.config_mgr.config["client"]["gamma"] = float(value)

        elif key == "monitor_index":
            self.config_mgr.config["client"]["monitor_index"] = int(value)
            print(f"[App] Monitor changed: {value}")
            needs_grabber_reload = True

        elif key == "depth":
            self.config_mgr.config["client"]["depth"] = int(value)
            needs_grabber_reload = True

        elif key.startswith("crop_"):
            side = key.replace("crop_", "")
            if "cropping" not in self.config_mgr.config["client"]:
                self.config_mgr.config["client"]["cropping"] = {}
            self.config_mgr.config["client"]["cropping"][side] = int(value)
            needs_grabber_reload = True

        # --- HARDWARE ---
        elif key == "brightness":
            self.config_mgr.config["hardware"]["brightness"] = int(
                value
            )  # Fixed assignment
            needs_esp_sync = True

        elif key == "smoothing_speed":
            self.config_mgr.config["hardware"]["smoothing_speed"] = int(value)
            needs_esp_sync = True

        # --- Reload Components ---
        if needs_grabber_reload and self.grabber:
            self.grabber.reload_config()

        # --- Sync (Realtime) ---
        if needs_esp_sync:
            cmd = {"cmd": key, "value": int(value)}
            self.esp_link.send_command(cmd)

    def preview_layout(self, layout_dict):
        """
        Sends the layout dimensions to the ESP for visual verification.
        Each side will be lit up in a different color.
        """
        cmd = {
            "cmd": "preview_layout",
            "top": int(layout_dict.get("top", 0)),
            "bottom": int(layout_dict.get("bottom", 0)),
            "left": int(layout_dict.get("left", 0)),
            "right": int(layout_dict.get("right", 0)),
        }

        if hasattr(self, "esp_link") and self.esp_link:
            self.esp_link.send_command(cmd)
        else:
            print(f"[App] Simulation: Previewing layout {cmd}")

    # ==========================================
    #         Hardware Synchronization
    # ==========================================

    def pull_hardware_config(self):
        """
        STARTUP ONLY: Fetches 'Source of Truth' (Hardware constraints) from ESP.
        Updates local config with num_leds, max_milliamps, etc.
        """
        print("[Sync] Requesting hardware config from ESP via Transmitter...")

        self.esp_link.send_command({"cmd": "get_config"})

        response = self.esp_link.wait_for_json(timeout=2.0)

        if response:
            print("[Sync] ESP responded! Updating local hardware.")
            if "hardware" in response:
                self.config_mgr.config["hardware"].update(response["hardware"])
            self.config_mgr._save_local_config(self.config_mgr.config)
        else:
            print("[Sync] No response from ESP. Using local cached config.")

    def push_hardware_config(self):
        """
        USER ACTION: Forces ESP to update its settings based on GUI.
        Called when 'Save Settings' is clicked.
        """
        print("[Sync] Pushing configuration TO ESP...")
        hw_config = self.config_mgr.config.get("hardware", {})

        payload = {"cmd": "save_config", "data": hw_config}

        self.esp_link.send_command(payload)
        self.config_mgr._save_local_config(self.config_mgr.config)
        print("[Sync] Hardware settings pushed and saved locally.")

    # ==========================================
    #            External Control
    # ==========================================

    def set_mode(self, new_mode: AppMode, **kwargs):
        if self.current_mode == new_mode:
            return

        print(f"[App] Switching: {self.current_mode.name} -> {new_mode.name}")
        cmd = {}

        if new_mode == AppMode.AMBILIGHT:
            cmd = {"cmd": "mode", "value": "ambilight"}
        elif new_mode == AppMode.RAINBOW:
            cmd = {"cmd": "mode", "value": "rainbow"}
        elif new_mode == AppMode.STATIC:
            color = kwargs.get("color", [255, 0, 0])
            cmd = {"cmd": "mode", "value": "static", "color": color}
        elif new_mode == AppMode.OFF:
            cmd = {"cmd": "mode", "value": "off"}

        self.esp_link.send_command(cmd)
        self.current_mode = new_mode
        self._notify_observers()

    def toggle(self):
        if self.current_mode == AppMode.OFF:
            self.set_mode(AppMode.AMBILIGHT)
            return "ON"
        else:
            self.set_mode(AppMode.OFF)
            return "OFF"

    def stop(self):
        print("[App] Total exit requested.")
        self.current_mode = AppMode.EXIT
        self._notify_observers()
        self.stop_all()

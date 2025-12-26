import threading
import time
from src.config_manager import ConfigManager
from src.screen_grabber import ScreenGrabber
from src.transmitters.serial_transmitter import SerialTransmitter
from src.transmitters.udp_transmitter import UdpTransmitter
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
        self.config_mgr.sync_with_esp()

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
            self.serial_comm = UdpTransmitter(host, udp_port)

        else:
            # Fallback to Serial
            com_port = str(self.config_mgr.get_nested("client", "com_port") or "COM3")
            baud = int(self.config_mgr.get_nested("hardware", "baud_rate") or 115200)

            print(f"[Main] Initializing Serial Transmitter ({com_port})...")
            self.serial_comm = SerialTransmitter(port=com_port, baud_rate=baud)

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
    #           Observer Pattern
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
    #           Thread Management
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
    #           Core Logic (State Aware)
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
                    self.serial_comm.send_colors(frame)
                    lights_physically_off = False

            else:
                # In any other mode (OFF, RAINBOW, STATIC), PC stops sending data
                if not lights_physically_off:
                    self.serial_comm.send_colors(black_frame)
                    lights_physically_off = True

                time.sleep(0.5)

        self.serial_comm.send_colors(black_frame)
        self.serial_comm.disconnect()
        print("[Worker] Logic loop finished.")

    # ==========================================
    #           External Control (State Machine)
    # ==========================================

    def set_mode(self, new_mode: AppMode, **kwargs):
        """
        Handles mode switching logic.
        1. Determines the correct JSON command for ESP.
        2. Sends the command.
        3. Updates internal state.
        4. Notifies GUI.
        """
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

        # Send the command to ESP
        self.serial_comm.send_command(cmd)

        # Update State & Notify
        self.current_mode = new_mode
        self._notify_observers()

    def toggle(self):
        """Helper for Tray Icon to toggle ON/OFF"""
        if self.current_mode == AppMode.OFF:
            self.set_mode(AppMode.AMBILIGHT)
            return "ON"
        else:
            self.set_mode(AppMode.OFF)
            return "OFF"

    def stop(self):
        """Called when user requests total exit (e.g., from Tray)"""
        print("[App] Total exit requested.")
        self.current_mode = AppMode.EXIT
        self._notify_observers()
        self.stop_all()

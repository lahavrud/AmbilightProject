import threading
import time
from .config_manager import ConfigManager
from .screen_grabber import ScreenGrabber
from .serial_comm import SerialCommunicator
from .system_tray import SystemTray

class AmbilightApp:
    """
    Main Application Controller.
    Manages the orchestration of:
    1. Hardware communication (Serial/ESP32).
    2. Screen capturing logic.
    3. Thread management (Worker & System Tray).
    4. State management.
    """

    def __init__(self):
        # --- 1. Component Initialization ---
        print("[Main] Initializing ConfigManager...")
        self.config_mgr = ConfigManager()
        self.config_mgr.load_local_config()
        self.config_mgr.sync_with_esp()

        # Load specific configurations
        hw_conf = self.config_mgr.config["hardware"]
        client_conf = self.config_mgr.config["client"]
        
        print(f"[Main] Initializing Serial Communicator on {client_conf['com_port']}...")
        self.serial_comm = SerialCommunicator(
            port=client_conf["com_port"],
            baud_rate=hw_conf["baud_rate"]
        )

        print("[Main] Initializing Screen Grabber...")
        self.grabber = ScreenGrabber(self.config_mgr)

        # --- 2. State Flags & Thread Handles ---
        self.is_running = True      # active flag: controls data transmission
        self.should_exit = False    # global exit flag: controls app lifecycle
        
        self.led_thread = None      # Handle for the LED processing thread
        self.tray_thread = None     # Handle for the System Tray thread
        self.tray = None            # Instance of the System Tray

    # ==========================================
    #           Thread Management
    # ==========================================

    def start_worker_thread(self):
        """
        Initializes and starts the main logic thread (LED processing) 
        in the background. Includes a check to prevent duplicate threads.
        """
        if self.led_thread is None or not self.led_thread.is_alive():
            self.led_thread = threading.Thread(target=self.worker_logic)
            self.led_thread.daemon = True  # Thread dies when main app closes
            self.led_thread.start()
            print("[Main] Worker (LEDs) thread started.")

    def start_tray_thread(self):
        """
        Initializes and starts the System Tray icon in a separate,
        non-blocking thread.
        """
        self.tray = SystemTray(self)
        self.tray_thread = threading.Thread(target=self.tray.run)
        self.tray_thread.daemon = True  # Thread dies when main app closes
        self.tray_thread.start()
        print("[Main] System Tray thread started.")

    def stop_all(self):
        """
        Graceful shutdown sequence.
        Signals all threads to stop and releases resources.
        """
        print("[Main] Stopping all threads...")
        self.should_exit = True  # Signal worker loop to break
        
        if self.tray:
            self.tray.stop()     # Signal tray icon to stop

    # ==========================================
    #           Core Logic (The Engine)
    # ==========================================

    def worker_logic(self):
        """
        The main operational loop running in a background thread.
        Responsibilities:
        1. Capture screen data via ScreenGrabber.
        2. Process and send data via SerialCommunicator.
        3. Handle 'Pause' state (send black frame).
        """
        print("[Worker] Logic loop started.")
        
        # Pre-calculate a black frame for the "Off/Paused" state
        total_leds = self.config_mgr.get_nested("hardware", "num_leds") or 60
        black_frame = b'\x00' * (total_leds * 3)
        lights_physically_off = False

        while not self.should_exit:
            if self.is_running:
                # 1. Capture and Process
                frame = self.grabber.get_frame_bytes()
                
                # 2. Transmit
                if frame:
                    self.serial_comm.send_colors(frame)
                    lights_physically_off = False
            
            else:
                # Handle Paused State
                # Send black frame once to turn off LEDs, then sleep
                if not lights_physically_off:
                    self.serial_comm.send_colors(black_frame)
                    lights_physically_off = True
                
                # Deep sleep to conserve CPU when paused
                time.sleep(0.5) 
        
        # Cleanup on exit
        self.serial_comm.send_colors(black_frame)
        self.serial_comm.close()
        print("[Worker] Logic loop finished.")

    # ==========================================
    #           External Control Methods
    # ==========================================

    def set_mode(self, mode_name):
        """
        Switches the operation mode.
        If 'ambilight': Activates PC-side processing.
        If other (e.g., 'rainbow'): Stops PC processing and sends JSON command to firmware.
        """
        if mode_name == "ambilight":
            self.is_running = True
            cmd = {"cmd": "mode", "value": "ambilight"}
        else:
            self.is_running = False
            # Short delay to allow the worker loop to send the last black frame
            time.sleep(0.1) 
            cmd = {"cmd": "mode", "value": mode_name}

        self.serial_comm.send_command(cmd)
        
    def toggle(self):
        """
        Toggles the active state of the Ambilight processing.
        Returns the new state as a string.
        """
        self.is_running = not self.is_running
        return "ON" if self.is_running else "OFF"

    def stop(self):
        """
        Public method called by external controllers (e.g., Tray 'Exit' button).
        Triggers the full shutdown sequence.
        """
        self.stop_all()
import threading
import time
from src.config_manager import ConfigManager
from src.screen_grabber import ScreenGrabber
from src.serial_comm import SerialCommunicator
from src.system_tray import SystemTray

class AmbilightApp:
    def __init__(self):
        # 1. Init Config & Sync with ESP
        print("[Main] Initializing Config...")
        self.config_mgr = ConfigManager()
        self.config_mgr.load_local_config()
        self.config_mgr.sync_with_esp()

        # 2. Extract specific configs
        hw_conf = self.config_mgr.config["hardware"]
        client_conf = self.config_mgr.config["client"]
        
        # 3. Init Serial Communication
        print(f"[Main] Initializing Serial on {client_conf['com_port']}...")
        self.serial_comm = SerialCommunicator(
            port=client_conf["com_port"],
            baud_rate=hw_conf["baud_rate"]
        )

        # 4. Init Screen Grabber
        print("[Main] Initializing Screen Grabber...")
        self.grabber = ScreenGrabber(self.config_mgr)

        # 5. State Flags
        self.is_running = True
        self.should_exit = False
        self.led_thread = None

    # --- Public Methods for GUI Control ---

    def set_mode(self, mode_name):
        """
        Changes the mode on the ESP32 (e.g., 'rainbow', 'static', 'ambilight')
        """
        if mode_name == "ambilight":
            self.is_running = True
            cmd = {"cmd": "mode", "value": "ambilight"}
        
        else:
            self.is_running = False
            time.sleep(0.1) 
            
            cmd = {"cmd": "mode", "value": mode_name}

        self.serial_comm.send_command(cmd)
        
    def toggle(self):
        """Toggles the running state on/off"""
        self.is_running = not self.is_running
        return "ON" if self.is_running else "OFF"

    def stop(self):
        """Signals the worker thread to exit"""
        self.should_exit = True
    
    # --- Worker Logic (Runs in a separate thread) ---

    def worker_logic(self):
        """The main infinite loop for processing frames"""
        print("[Worker] Started.")
        
        # Prepare black frame for "off" state
        total_leds = self.config_mgr.get_nested("hardware", "num_leds") or 60
        black_frame = b'\x00' * (total_leds * 3)
        lights_physically_off = False

        while not self.should_exit:
            if self.is_running:
                frame = self.grabber.get_frame_bytes()
                
                if frame:
                    self.serial_comm.send_colors(frame)
                    lights_physically_off = False
                
            
            else:
                # Paused state
                if not lights_physically_off:
                    print("[Worker] Paused. Sending black frame.")
                    self.serial_comm.send_colors(black_frame)
                    lights_physically_off = True
                
                # Deep sleep when paused
                time.sleep(0.5)
        
        # Cleanup
        self.serial_comm.send_colors(black_frame)
        self.serial_comm.close()
        print("[Worker] Stopped.")

    def start(self):
        """Starts the worker thread and the system tray"""
        # 1. Start the Logic Thread (Non-blocking)
        self.led_thread = threading.Thread(target=self.worker_logic)
        self.led_thread.daemon = True
        self.led_thread.start()
        
        # 2. Start the System Tray (Blocking)
        # We pass 'self' so the tray can control the app
        tray = SystemTray(app_controller=self)
        tray.run()

if __name__ == "__main__":
    app = AmbilightApp()
    app.start()

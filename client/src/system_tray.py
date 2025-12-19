import pystray
from PIL import Image
import os
import sys

class SystemTray:
    def __init__(self, app_controller):
        self.app = app_controller
        self.icon = None

    def _get_icon_image(self):
        """Load icon safely with fallback"""
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS # type: ignore
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
                base_path = os.path.dirname(base_path) # Go up one level from src

            icon_path = os.path.join(base_path, "icon.png")
            return Image.open(icon_path)
        except Exception as e:
            print(f"[Tray] Icon missing, using default red square. ({e})")
            return Image.new('RGB', (64, 64), color='red')

    def _on_toggle(self, icon, item):
        new_state = self.app.toggle()
        print(f"[Tray] Toggled. New State: {new_state}")

    def _on_exit(self, icon, item):
        print("[Tray] Exit requested.")
        self.app.stop()
        icon.stop()

    def run(self):
        image = self._get_icon_image()
        
        self.icon = pystray.Icon("Ambilight", image, menu=pystray.Menu(
            pystray.MenuItem("Toggle On/Off", self._on_toggle),
            pystray.MenuItem("Exit", self._on_exit)
        ))
        
        print("[Tray] System Tray started.")
        self.icon.run()
    
    def stop(self):
        if self.icon:
            self.icon.stop()
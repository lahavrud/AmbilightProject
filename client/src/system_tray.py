import pystray
from PIL import Image
import os
import sys
from .models import AppMode

class SystemTray:
    def __init__(self, app_controller):
        self.app = app_controller
        self.icon = None
        
        # --- Observer Registration ---
        self.app.register_observer(self.on_mode_changed)

    def on_mode_changed(self, new_mode: AppMode):
        """
        Callback triggered by the AppController whenever the state changes.
        """
        print(f"[Tray] Observer notified: App is now in {new_mode.name}")
        
        # NOTE: Later we can use self.icon.update_menu() here 
        # to show a checkmark next to the active mode.

    def _get_icon_image(self):
        """Load icon safely with fallback"""
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS # type: ignore
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
                base_path = os.path.dirname(base_path)

            icon_path = os.path.join(base_path, "icon.png")
            return Image.open(icon_path)
        except Exception as e:
            print(f"[Tray] Icon missing, using default red square. ({e})")
            return Image.new('RGB', (64, 64), color='red')

    def _on_toggle(self, icon, item):
        """Triggered when user clicks 'Toggle' in the tray menu"""
        # The controller will change the state and then notify us back 
        # via the 'on_mode_changed' callback.
        new_state_str = self.app.toggle() 
        print(f"[Tray] Toggle action requested. App replied: {new_state_str}")

    def _on_exit(self, icon, item):
        print("[Tray] Exit requested via menu.")
        self.app.stop()
        icon.stop()

    def run(self):
        image = self._get_icon_image()
        
        # We can define more menu items now that we have AppMode
        self.icon = pystray.Icon("Ambilight", image, menu=pystray.Menu(
            pystray.MenuItem("Toggle On/Off", self._on_toggle),
            pystray.MenuItem("Ambilight Mode", lambda: self.app.set_mode(AppMode.AMBILIGHT)),
            pystray.MenuItem("Rainbow Mode", lambda: self.app.set_mode(AppMode.RAINBOW)),
            pystray.MenuItem("Exit", self._on_exit)
        ))
        
        print("[Tray] System Tray started and waiting for updates.")
        self.icon.run()
    
    def stop(self):
        if self.icon:
            self.icon.stop()
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
        if self.icon:
            self.icon.update_menu()
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

    def _make_menu(self):
        return pystray.Menu(
            pystray.MenuItem(
                # --- Dynamic Toggle Button ---
                text=lambda item: "Turn Off" if self.app.current_mode != AppMode.OFF else "Turn On",
                action=self._on_toggle,
                default=True
            ),

            pystray.Menu.SEPARATOR,

            # --- Modes (Radio Buttons) ---
            pystray.MenuItem(
                text="Ambilight Mode",
                action=lambda: self.app.set_mode(AppMode.AMBILIGHT),
                checked=lambda item: self.app.current_mode == AppMode.AMBILIGHT,
                radio=True
            ),
            pystray.MenuItem(
                text="Rainbow Mode",
                action=lambda: self.app.set_mode(AppMode.RAINBOW),
                checked=lambda item: self.app.current_mode == AppMode.RAINBOW,
                radio=True
            ),
            pystray.MenuItem(
                text="Static Mode (Red)",
                action=lambda: self.app.set_mode(AppMode.STATIC),
                checked=lambda item: self.app.current_mode == AppMode.STATIC,
                radio=True
            ),

            pystray.Menu.SEPARATOR,

            pystray.MenuItem("Exit", self._on_exit)

        )

    def run(self):
        image = self._get_icon_image()
        
        self.icon = pystray.Icon(
            "Ambilight",
            image,
            menu=self._make_menu()
        )
        
        print("[Tray] System Tray started and waiting for updates.")
        self.icon.run()
    
    def stop(self):
        if self.icon:
            self.icon.stop()
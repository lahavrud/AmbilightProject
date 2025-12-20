import customtkinter as ctk
from ..models import AppMode

class MainWindow(ctk.CTk):
    def __init__(self, app_controller):
        super().__init__()
        
        self.app = app_controller
        
        # --- Basic Settings ---
        self.title("Ambilight Studio")
        self.geometry("600x500")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Dictionary to store button references for easy styling
        self.mode_buttons = {}

        self._setup_ui()

        # --- Observer Registration ---
        # We tell the app: "Call sync_ui_to_mode whenever the state changes"
        self.app.register_observer(self.sync_ui_to_mode)
        
        # Initial sync to reflect current state on startup
        self.sync_ui_to_mode(self.app.current_mode)

    def _setup_ui(self):
        # Title
        self.lbl_title = ctk.CTkLabel(self, text="Ambilight Control", font=("Roboto", 24, "bold"))
        self.lbl_title.pack(pady=20)

        # Main Power Button (Toggles between OFF and last active mode/Ambilight)
        self.btn_power = ctk.CTkButton(
            self, 
            text="POWER OFF",
            command=self.app.toggle, # Uses the simple toggle we built
            width=200,
            height=50,
            font=("Roboto", 18, "bold"),
            fg_color="#444444",
            hover_color="#333333"
        )
        self.btn_power.pack(pady=20)

        # Modes Zone
        self.frame_modes = ctk.CTkFrame(self)
        self.frame_modes.pack(pady=20, padx=20, fill="x")

        ctk.CTkLabel(self.frame_modes, text="Lighting Modes:", font=("Roboto", 14)).pack(pady=10)
        
        # Define Modes
        modes_config = [
            ("Screen Mirror", AppMode.AMBILIGHT),
            ("Rainbow", AppMode.RAINBOW),
            ("Static Red", AppMode.STATIC)
        ]

        # Create buttons dynamically
        for text, mode in modes_config:
            btn = ctk.CTkButton(
                self.frame_modes, 
                text=text, 
                command=lambda m=mode: self.app.set_mode(m),
                fg_color="#3b3b3b" # Default dark gray
            )
            btn.pack(side="left", padx=10, pady=20, expand=True)
            self.mode_buttons[mode] = btn

    def sync_ui_to_mode(self, current_mode: AppMode):
        """
        The Observer Callback.
        Updates button colors and text based on the active state.
        """
        print(f"[GUI] Syncing UI to mode: {current_mode.name}")

        # 1. Exit Window
        if current_mode == AppMode.EXIT:
            print("[GUI] Received Exit signal, closing window...")
            self.quit()
            return

        # 2. Update Mode Buttons
        for mode, btn in self.mode_buttons.items():
            if mode == current_mode:
                # Highlight active mode
                btn.configure(fg_color="#1f538d", border_width=2, border_color="white")
            else:
                # Reset others
                btn.configure(fg_color="#3b3b3b", border_width=0)

        # 3. Update Power Button appearance
        if current_mode == AppMode.OFF:
            self.btn_power.configure(text="TURN ON", fg_color="green", hover_color="darkgreen")
        else:
            self.btn_power.configure(text="TURN OFF", fg_color="red", hover_color="darkred")

    def on_close(self):
        """Clean shutdown protocol"""
        print("[GUI] Closing window...")
        self.app.stop_all()
        self.destroy()
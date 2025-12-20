import customtkinter as ctk
from src.models import AppMode

class DashboardTab(ctk.CTkFrame):
    def __init__(self, parent, app_controller):
        super().__init__(parent)
        self.app = app_controller
        self.mode_buttons = {}

        self._setup_ui()
        
        self.app.register_observer(self.update_state)
        
        self.update_state(self.app.current_mode)

    def _setup_ui(self):
        # -- Power Button --
        self.btn_power = ctk.CTkButton(
            self, 
            text="POWER OFF",
            command=self.app.toggle,
            width=200, height=50,
            font=("Roboto", 18, "bold"),
            fg_color="#444444", hover_color="#333333"
        )
        self.btn_power.pack(pady=30)

        # -- Modes Zone --
        ctk.CTkLabel(self, text="Select Mode:", font=("Roboto", 16)).pack(pady=(10, 5))
        
        frame_modes = ctk.CTkFrame(self, fg_color="transparent")
        frame_modes.pack(pady=10, padx=20, fill="x")

        modes_config = [
            ("Screen Mirror", AppMode.AMBILIGHT),
            ("Rainbow", AppMode.RAINBOW),
            ("Static Red", AppMode.STATIC)
        ]

        for text, mode in modes_config:
            btn = ctk.CTkButton(
                frame_modes, 
                text=text, 
                command=lambda m=mode: self.app.set_mode(m),
                fg_color="#3b3b3b", height=40
            )
            btn.pack(side="left", padx=10, pady=10, expand=True)
            self.mode_buttons[mode] = btn

    def update_state(self, current_mode: AppMode):
        
        if current_mode == AppMode.EXIT:
            return

        for mode, btn in self.mode_buttons.items():
            if mode == current_mode:
                btn.configure(fg_color="#1f538d", border_width=2, border_color="white")
            else:
                btn.configure(fg_color="#3b3b3b", border_width=0)

        if current_mode == AppMode.OFF:
            self.btn_power.configure(text="TURN ON", fg_color="green", hover_color="darkgreen")
        else:
            self.btn_power.configure(text="TURN OFF", fg_color="red", hover_color="darkred")
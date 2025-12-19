import customtkinter as ctk
import threading

class MainWindow(ctk.CTk):
    def __init__(self, app_controller):
        super().__init__()
        
        self.app = app_controller
        
        # Basic Settings   
        self.title("Ambilight Studio")
        self.geometry("600x500")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self._setup_ui()
        
        self.update_status_lights()

    def _setup_ui(self):
        # Title
        self.lbl_title = ctk.CTkLabel(self, text="Ambilight Control", font=("Roboto", 24, "bold"))
        self.lbl_title.pack(pady=20)

        # START/STOP Button
        self.btn_toggle = ctk.CTkButton(
            self, 
            text="STOP" if self.app.is_running else "START",
            command=self.on_toggle_click,
            width=200,
            height=50,
            font=("Roboto", 18),
            fg_color="red" if self.app.is_running else "green",
            hover_color="darkred" if self.app.is_running else "darkgreen"
        )
        self.btn_toggle.pack(pady=20)

        # Modes Zone
        self.frame_modes = ctk.CTkFrame(self)
        self.frame_modes.pack(pady=20, padx=20, fill="x")

        ctk.CTkLabel(self.frame_modes, text="Lighting Modes:").pack(pady=5)
        
        # Modes Buttons
        modes = [("Screen Mirror", "ambilight"), ("Rainbow", "rainbow"), ("Static Red", "static_red")]
        for text, mode in modes:
            ctk.CTkButton(
                self.frame_modes, 
                text=text, 
                command=lambda m=mode: self.on_mode_click(m)
            ).pack(side="left", padx=10, pady=10, expand=True)

    def on_toggle_click(self):
        # Toggle Logic
        new_state = self.app.toggle() 
        self.update_status_lights()

    def on_mode_click(self, mode):
        print(f"[GUI] Switching to mode: {mode}")
        
        if mode == "ambilight":
            self.app.set_mode("ambilight")
        elif mode == "rainbow":
            self.app.set_mode("rainbow")
        elif mode == "static_red":
            self.app.serial_comm.send_command({
                "cmd": "mode", 
                "value": "static", 
                "color": [255, 0, 0]
            })
            self.app.is_running = False
        
        self.update_status_lights()

    def update_status_lights(self):
        if self.app.is_running:
            self.btn_toggle.configure(text="STOP AMBILIGHT", fg_color="red", hover_color="darkred")
        else:
            self.btn_toggle.configure(text="START AMBILIGHT", fg_color="green", hover_color="darkgreen")

    def on_close(self):
        self.app.stop()
        self.destroy()
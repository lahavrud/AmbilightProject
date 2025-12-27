import customtkinter as ctk


class CalibrationTab(ctk.CTkFrame):
    def __init__(self, parent, app_controller):
        super().__init__(parent)
        self.app = app_controller

        self._setup_ui()

    def _setup_ui(self):
        # --- Title ---
        lbl_title = ctk.CTkLabel(
            self,
            text="Calibration Area",
            font=("Roboto", 20, "bold"),
        )
        lbl_title.pack(pady=(20, 10))

        # --- Gamma Slider Section ---
        lbl_gamma = ctk.CTkLabel(self, text="Gamma Correction (1.0 - 3.0):")
        lbl_gamma.pack(pady=(10, 0))

        current_gamma = self.app.config_mgr.get_nested("client", "gamma") or 2.2

        self.slider_gamma = ctk.CTkSlider(
            self, from_=1, to=3, number_of_steps=20, command=self.on_gamma_change
        )

        self.slider_gamma.set(current_gamma)
        self.slider_gamma.pack(pady=5)

        self.lbl_gamma_val = ctk.CTkLabel(self, text=f"{current_gamma:.1f}")
        self.lbl_gamma_val.pack()

        # --- Controls Container ---
        controls_frame = ctk.CTkFrame(
            self,
            fg_color="#2b2b2b",
            corner_radius=15,
            border_width=1,
            border_color="gray",
        )
        self.controls = controls_frame  # שומרים רפרנס כדי למקם ב-Resize
        self.controls.place(relx=0.5, rely=0.95, anchor="s", relwidth=0.9)

        # 1. Monitor Selection Dropdown
        lbl_mon = ctk.CTkLabel(
            controls_frame, text="Source Display:", font=("Arial", 12, "bold")
        )
        lbl_mon.pack(anchor="w", padx=20, pady=(10, 0))

        monitors = self.app.grabber.get_monitors_list()

        current_idx = self.app.config_mgr.get_nested("client", "monitor_index") or 1
        current_val = f"Monitor {current_idx}"
        if current_val not in monitors:
            current_val = monitors[0]  # Fallback

        self.monitor_dropdown = ctk.CTkOptionMenu(
            controls_frame, values=monitors, command=self.on_monitor_change, width=200
        )
        self.monitor_dropdown.set(current_val)
        self.monitor_dropdown.pack(padx=20, pady=(0, 10), anchor="w")

    def on_gamma_change(self, value):
        """Gets called every move of the slide"""
        self.lbl_gamma_val.configure(text=f"{value:.1f}")
        self.app.update_setting("gamma", value)

    def on_monitor_change(self, choice):
        # choice is string like "Monitor 2" -> we need int 2
        idx = int(choice.split(" ")[1])
        self.app.update_setting("monitor_index", idx)
        # self.after(200, self.update_snapshot)

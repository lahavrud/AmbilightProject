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

    def on_gamma_change(self, value):
        """Gets called every move of the slide"""
        self.lbl_gamma_val.configure(text=f"{value:.1f}")
        self.app.update_settings("gamma", value)

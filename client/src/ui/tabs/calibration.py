import customtkinter as ctk


class CalibrationTab(ctk.CTkFrame):
    def __init__(self, parent, app_controller):
        super().__init__(parent)
        self.app = app_controller

        self._setup_ui()

    def _setup_ui(self):
        lbl_info = ctk.CTkLabel(
            self,
            text="Calibration Area\n(Here we will adjust Screen Crop & Depth)",
            font=("Roboto", 20),
            text_color="gray",
        )
        lbl_info.pack(expand=True)

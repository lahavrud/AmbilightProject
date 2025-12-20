import customtkinter as ctk
from src.models import AppMode

from .tabs.dashboard import DashboardTab
from .tabs.calibration import CalibrationTab

class MainWindow(ctk.CTk):
    def __init__(self, app_controller):
        super().__init__()
        
        self.app = app_controller
        
        self.title("Ambilight Studio")
        self.geometry("700x550")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self._init_layout()

        self.app.register_observer(self.on_app_state_change)

    def _init_layout(self):
        self.lbl_title = ctk.CTkLabel(self, text="Ambilight Studio", font=("Roboto", 24, "bold"))
        self.lbl_title.pack(pady=(20, 10))

        self.tab_view = ctk.CTkTabview(self, width=650, height=400)
        self.tab_view.pack(pady=10, padx=20, fill="both", expand=True)

        self.tab_view.add("Dashboard")
        self.tab_view.add("Calibration")

        
        self.dashboard = DashboardTab(parent=self.tab_view.tab("Dashboard"), app_controller=self.app)
        self.dashboard.pack(fill="both", expand=True)

        self.calibration = CalibrationTab(parent=self.tab_view.tab("Calibration"), app_controller=self.app)
        self.calibration.pack(fill="both", expand=True)

        self.tab_view.set("Dashboard")

    def on_app_state_change(self, current_mode: AppMode):
        if current_mode == AppMode.EXIT:
            self.quit()

    def on_close(self):
        self.app.stop_all()
        self.quit()
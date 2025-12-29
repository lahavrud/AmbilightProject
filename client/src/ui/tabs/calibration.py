import customtkinter as ctk

from src.ui.windows.screen_editor import ScreenEditor


class CalibrationTab(ctk.CTkFrame):
    def __init__(self, parent, app_controller):
        super().__init__(parent)
        self.app = app_controller
        self.editor_window = None  # משתנה לשמירת רפרנס לחלון

        self._setup_ui()

    def _setup_ui(self):
        lbl_info = ctk.CTkLabel(
            self,
            text="Calibration Area",
            font=("Roboto", 20, "bold"),
        )
        lbl_info.pack(pady=(20, 10))

        btn_open = ctk.CTkButton(
            self,
            text="Open Screen Editor",
            command=self.open_editor,
            height=40,
            fg_color="#E67E22",
            hover_color="#D35400",
        )
        btn_open.pack(pady=10)

    def open_editor(self):
        if self.editor_window is not None and self.editor_window.winfo_exists():
            self.editor_window.lift()
            self.editor_window.focus_force()
            return

        self.editor_window = ScreenEditor(self.winfo_toplevel(), self.app)

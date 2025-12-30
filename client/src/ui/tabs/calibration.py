import customtkinter as ctk
from src.ui.windows.screen_editor import ScreenEditor
from src.ui.windows.corner_wizard import CornerWizard  # ייבוא החלון החדש


class CalibrationTab(ctk.CTkFrame):
    """
    Tab responsible for geometric calibration (Screen Editor & Corner Wizard) and
    performance tuning (Gamma, Brightness, Smoothing).
    """

    def __init__(self, parent, app_controller):
        super().__init__(parent)
        self.app = app_controller
        self.editor_window = None
        self.wizard_window = None

        self._setup_ui()

    def _setup_ui(self):
        # --- Header ---
        ctk.CTkLabel(
            self, text="Calibration & Performance", font=("Roboto", 20, "bold")
        ).pack(pady=(20, 10))

        # --- Geometric Calibration Section ---
        geo_frame = ctk.CTkFrame(self, fg_color="transparent")
        geo_frame.pack(pady=10)

        ctk.CTkButton(
            geo_frame,
            text="Adjust Screen Area",
            command=self.open_editor,
            height=40,
            width=200,
            fg_color="#E67E22",
            hover_color="#D35400",
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            geo_frame,
            text="Map LED Corners",
            command=self.open_wizard,
            height=40,
            width=200,
            fg_color="#3498DB",
            hover_color="#2980B9",
        ).pack(side="left", padx=10)

        # Visual Separator
        ctk.CTkFrame(self, height=2, fg_color="#333").pack(fill="x", padx=20, pady=15)

        # =========================================
        #             Performance Tuning
        # =========================================
        # Gamma
        current_gamma = self.app.config_mgr.get_nested("client", "gamma") or 2.2
        self._add_slider_control(
            "Gamma Correction", "gamma", current_gamma, 1.0, 3.0, 0.1
        )

        # Brightness
        current_bright = self.app.config_mgr.get_nested("hardware", "brightness") or 50
        self._add_slider_control(
            "LED Brightness", "brightness", current_bright, 1, 100, 1, suffix="%"
        )

        # Smoothing
        current_smooth = (
            self.app.config_mgr.get_nested("hardware", "smoothing_speed") or 20
        )
        self._add_slider_control(
            "Smoothing Speed", "smoothing_speed", current_smooth, 1, 100, 1
        )

        # --- Save Button ---
        ctk.CTkButton(
            self,
            text="Save Settings to Disk",
            command=self.save_settings,
            fg_color="#27AE60",
            hover_color="#2ECC71",
        ).pack(side="bottom", pady=20)

    def _add_slider_control(
        self, label_text, config_key, current_val, min_val, max_val, step, suffix=""
    ):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=30, pady=5)

        ctk.CTkLabel(row, text=label_text, width=140, anchor="w").pack(side="left")

        val_label = ctk.CTkLabel(
            row,
            text=f"{current_val}{suffix}",
            width=40,
            anchor="e",
            text_color="#3498DB",
        )
        val_label.pack(side="right")

        slider = ctk.CTkSlider(
            row,
            from_=min_val,
            to=max_val,
            number_of_steps=(max_val - min_val) / step,
            command=lambda v: self._on_slider_change(v, config_key, val_label, suffix),
        )
        slider.set(current_val)
        slider.pack(side="left", expand=True, fill="x", padx=10)

    def _on_slider_change(self, value, key, label_widget, suffix):
        if isinstance(value, float) and value % 1 != 0:
            display_val = f"{value:.1f}"
            final_val = float(value)
        else:
            display_val = f"{int(value)}"
            final_val = int(value)

        label_widget.configure(text=f"{display_val}{suffix}")
        self.app.update_setting(key, final_val)

    def open_editor(self):
        """Opens or focuses the Screen Editor window."""
        if self.editor_window is not None and self.editor_window.winfo_exists():
            self.editor_window.lift()
            self.editor_window.focus_force()
            return
        self.editor_window = ScreenEditor(self.winfo_toplevel(), self.app)

    def open_wizard(self):
        """Opens or focuses the Corner Wizard window."""
        if self.wizard_window is not None and self.wizard_window.winfo_exists():
            self.wizard_window.lift()
            self.wizard_window.focus_force()
            return

        if self.editor_window and self.editor_window.winfo_exists():
            self.editor_window.destroy()

        self.wizard_window = CornerWizard(self.winfo_toplevel(), self.app)

    def save_settings(self):
        self.app.config_mgr._save_local_config(self.app.config_mgr.config)
        print("[UI] Settings saved manually.")

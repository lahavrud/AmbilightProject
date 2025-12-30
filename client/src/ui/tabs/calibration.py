import customtkinter as ctk
from src.ui.windows.screen_editor import ScreenEditor


class CalibrationTab(ctk.CTkFrame):
    """
    Tab responsible for geometric calibration (Screen Editor) and
    performance tuning (Gamma, Brightness, Smoothing).
    """

    def __init__(self, parent, app_controller):
        super().__init__(parent)
        self.app = app_controller
        self.editor_window = None  # Reference to the popup window

        self._setup_ui()

    def _setup_ui(self):
        # --- Header ---
        ctk.CTkLabel(
            self, text="Calibration & Performance", font=("Roboto", 20, "bold")
        ).pack(pady=(20, 10))

        # --- Screen Editor Button ---
        ctk.CTkButton(
            self,
            text="Open Screen Editor",
            command=self.open_editor,
            height=40,
            fg_color="#E67E22",
            hover_color="#D35400",
        ).pack(pady=10)

        # Visual Separator
        ctk.CTkFrame(self, height=2, fg_color="#333").pack(fill="x", padx=20, pady=10)

        # =========================================
        #              Gamma (Color)
        # =========================================
        # Range: 1.0 to 3.0
        current_gamma = self.app.config_mgr.get_nested("client", "gamma") or 2.2
        self._add_slider_control(
            label_text="Gamma Correction",
            config_key="gamma",
            current_val=current_gamma,
            min_val=1.0,
            max_val=3.0,
            step=0.1,
        )

        # =========================================
        #            Brightness (Hardware)
        # =========================================
        # Range: 1% to 100%
        current_bright = self.app.config_mgr.get_nested("hardware", "brightness") or 50
        self._add_slider_control(
            label_text="LED Brightness",
            config_key="brightness",
            current_val=current_bright,
            min_val=1,
            max_val=100,
            step=1,
            suffix="%",
        )

        # =========================================
        #           Smoothing Speed (Hardware)
        # =========================================
        # Range: 1 (Slow/Fluid) to 100 (Fast/Snappy)
        current_smooth = (
            self.app.config_mgr.get_nested("hardware", "smoothing_speed") or 20
        )
        self._add_slider_control(
            label_text="Smoothing Speed",
            config_key="smoothing_speed",
            current_val=current_smooth,
            min_val=1,
            max_val=100,
            step=1,
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
        """
        Helper method to create a standardized row with Label, Slider, and Value display.
        """
        # Container Frame
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=30, pady=5)

        # Label (Left)
        ctk.CTkLabel(row, text=label_text, width=140, anchor="w").pack(side="left")

        # Value Label (Right) - Created before slider so we can pass it to the callback
        val_label = ctk.CTkLabel(
            row,
            text=f"{current_val}{suffix}",
            width=40,
            anchor="e",
            text_color="#3498DB",
        )
        val_label.pack(side="right")

        # Slider (Center)
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
        """
        Generic handler for all sliders.
        Updates the label text and sends the new value to AppController.
        """
        # Format display (int vs float)
        if isinstance(value, float) and value % 1 != 0:
            display_val = f"{value:.1f}"
            final_val = float(value)
        else:
            display_val = f"{int(value)}"
            final_val = int(value)

        # Update UI Label
        label_widget.configure(text=f"{display_val}{suffix}")

        # Update Logic (AppController handles routing to 'client' or 'hardware' based on key)
        self.app.update_setting(key, final_val)

    def save_settings(self):
        """Manually triggers a save to config.json"""
        self.app.config_mgr._save_local_config(self.app.config_mgr.config)
        print("[UI] Settings saved manually.")

    def open_editor(self):
        """Opens or focuses the Screen Editor window."""
        if self.editor_window is not None and self.editor_window.winfo_exists():
            self.editor_window.lift()
            self.editor_window.focus_force()
            return

        self.editor_window = ScreenEditor(self.winfo_toplevel(), self.app)

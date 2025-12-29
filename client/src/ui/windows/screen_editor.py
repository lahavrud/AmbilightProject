import tkinter as tk
import customtkinter as ctk


class ScreenEditor(tk.Toplevel):
    def __init__(self, parent, app_controller):
        super().__init__(parent)
        self.app = app_controller

        self.title("Screen Editor")

        # --- 1. Start Invisible (Ghost Mode) ---
        self.attributes("-alpha", 0.0)

        # --- 2. Window Setup ---
        self.overrideredirect(True)
        self.configure(bg="black")
        self.attributes("-topmost", True)

        # --- 3. Geometry ---
        monitor = self.app.grabber.get_monitor_geometry()
        self.phys_w = monitor["width"]
        self.phys_h = monitor["height"]
        geo = f"{self.phys_w}x{self.phys_h}+{monitor['left']}+{monitor['top']}"
        self.geometry(geo)

        # --- 4. Canvas ---
        self.canvas = tk.Canvas(self, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.bind("<Escape>", lambda e: self.destroy())

        # --- 5. UI & Logic ---
        self._setup_ui()
        self._draw_overlay()

        # Force layout calculation
        self.update_idletasks()

        # --- 6. Reveal ---
        self.after(150, self.reveal_window)

    def reveal_window(self):
        """Reveal window smoothly to prevent flicker."""
        self.attributes("-alpha", 0.7)
        self.after(50, lambda: self.focus_force())

    # --- Monkey Patch (Required for CTK) ---
    def block_update_dimensions_event(self):
        pass

    def unblock_update_dimensions_event(self):
        pass

    # ---------------------------------------

    def _setup_ui(self):
        # Control Frame
        self.controls = ctk.CTkFrame(
            self,
            fg_color="#1a1a1a",
            border_width=2,
            border_color="#333",
            corner_radius=15,
        )
        self.controls.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            self.controls, text="Calibration", font=("Roboto", 18, "bold")
        ).pack(pady=(15, 5), padx=20)

        # Monitor Selector
        monitors = self.app.grabber.get_monitors_list()
        current_idx = self.app.config_mgr.get_nested("client", "monitor_index") or 1
        current_val = f"Monitor {current_idx}"
        if current_val not in monitors:
            current_val = monitors[0] if monitors else "Monitor 1"

        self.combo_mon = ctk.CTkOptionMenu(
            self.controls, values=monitors, command=self.on_monitor_change, width=200
        )
        self.combo_mon.set(current_val)
        self.combo_mon.pack(pady=5, padx=20)

        # Sliders
        self.sliders = {}
        self.labels = {}
        crop_cfg = self.app.config_mgr.get_nested("client", "cropping") or {}

        self._add_slider("Top", "crop_top", crop_cfg.get("top", 0), self.phys_h // 2)
        self._add_slider(
            "Bottom", "crop_bottom", crop_cfg.get("bottom", 0), self.phys_h // 2
        )
        self._add_slider("Left", "crop_left", crop_cfg.get("left", 0), self.phys_w // 2)
        self._add_slider(
            "Right", "crop_right", crop_cfg.get("right", 0), self.phys_w // 2
        )

        ctk.CTkFrame(self.controls, height=2, fg_color="#333").pack(
            fill="x", padx=10, pady=10
        )

        current_depth = self.app.config_mgr.get_nested("client", "depth") or 100
        self._add_slider("Depth", "depth", current_depth, self.phys_h // 3)

        # Buttons
        btn_frame = ctk.CTkFrame(self.controls, fg_color="transparent")
        btn_frame.pack(pady=20, fill="x", padx=20)

        ctk.CTkButton(
            btn_frame,
            text="Reset",
            command=self.reset_crops,
            fg_color="#C0392B",
            hover_color="#E74C3C",
            width=80,
        ).pack(side="left", padx=(0, 10), expand=True)

        ctk.CTkButton(
            btn_frame,
            text="Done (ESC)",
            command=self.destroy,
            fg_color="#444",
            hover_color="#333",
            width=80,
        ).pack(side="right", expand=True)

    def _add_slider(self, label_text, config_key, current_val, limit):
        row = ctk.CTkFrame(self.controls, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=2)
        ctk.CTkLabel(row, text=label_text, width=50, anchor="w").pack(side="left")

        val_label = ctk.CTkLabel(
            row, text=f"{current_val} px", width=60, anchor="e", text_color="#E67E22"
        )
        val_label.pack(side="right")
        self.labels[config_key] = val_label

        slider = ctk.CTkSlider(
            row,
            from_=0,
            to=limit,
            number_of_steps=limit,
            command=lambda value,
            key=config_key,
            label=val_label: self._on_slider_change(value, key, label),
        )
        slider.set(current_val)
        slider.pack(side="left", expand=True, padx=10)
        self.sliders[config_key] = slider

    def _on_slider_change(self, value, key, label):
        val = int(value)
        label.configure(text=f"{val} px")

        # This calls AppController -> ConfigManager -> ScreenGrabber reload
        if key == "depth":
            self.app.update_setting("depth", val)
        else:
            simple_key = key.replace("crop_", "")
            self.app.update_setting(f"crop_{simple_key}", val)

        self._draw_overlay()

    def reset_crops(self):
        for key, slider in self.sliders.items():
            if key == "depth":
                slider.set(100)
                self.labels[key].configure(text="100 px")
                self.app.update_setting("depth", 100)
            else:
                slider.set(0)
                self.labels[key].configure(text="0 px")
                simple_key = key.replace("crop_", "")
                self.app.update_setting(f"crop_{simple_key}", 0)
        self._draw_overlay()

    def _draw_overlay(self):
        self.canvas.delete("all")
        if not hasattr(self, "sliders"):
            return

        t_crop = int(self.sliders["crop_top"].get())
        b_crop = int(self.sliders["crop_bottom"].get())
        l_crop = int(self.sliders["crop_left"].get())
        r_crop = int(self.sliders["crop_right"].get())
        d_crop = int(self.sliders["depth"].get())

        w, h = self.phys_w, self.phys_h

        # Black zones
        self.canvas.create_rectangle(
            0, 0, w, t_crop, fill="black", stipple="gray50", width=0
        )
        self.canvas.create_rectangle(
            0, h - b_crop, w, h, fill="black", stipple="gray50", width=0
        )
        self.canvas.create_rectangle(
            0, t_crop, l_crop, h - b_crop, fill="black", stipple="gray50", width=0
        )
        self.canvas.create_rectangle(
            w - r_crop, t_crop, w, h - b_crop, fill="black", stipple="gray50", width=0
        )

        # Green zones
        sampling_color = "#2ECC71"
        sampling_stipple = "gray25"
        self.canvas.create_rectangle(
            l_crop,
            t_crop,
            w - r_crop,
            t_crop + d_crop,
            fill=sampling_color,
            stipple=sampling_stipple,
            width=0,
        )
        self.canvas.create_rectangle(
            l_crop,
            h - b_crop - d_crop,
            w - r_crop,
            h - b_crop,
            fill=sampling_color,
            stipple=sampling_stipple,
            width=0,
        )
        self.canvas.create_rectangle(
            l_crop,
            t_crop + d_crop,
            l_crop + d_crop,
            h - b_crop - d_crop,
            fill=sampling_color,
            stipple=sampling_stipple,
            width=0,
        )
        self.canvas.create_rectangle(
            w - r_crop - d_crop,
            t_crop + d_crop,
            w - r_crop,
            h - b_crop - d_crop,
            fill=sampling_color,
            stipple=sampling_stipple,
            width=0,
        )

        # Outlines & Corners
        self.canvas.create_rectangle(
            l_crop, t_crop, w - r_crop, h - b_crop, outline="#00AAFF", width=2
        )
        self.canvas.create_rectangle(
            l_crop + d_crop,
            t_crop + d_crop,
            w - r_crop - d_crop,
            h - b_crop - d_crop,
            outline="#FF3333",
            width=1,
            dash=(4, 4),
        )

        length = 20
        color = "#00AAFF"
        width = 3
        self.canvas.create_line(
            l_crop, t_crop, l_crop + length, t_crop, fill=color, width=width
        )
        self.canvas.create_line(
            l_crop, t_crop, l_crop, t_crop + length, fill=color, width=width
        )
        self.canvas.create_line(
            w - r_crop, t_crop, w - r_crop - length, t_crop, fill=color, width=width
        )
        self.canvas.create_line(
            w - r_crop, t_crop, w - r_crop, t_crop + length, fill=color, width=width
        )
        self.canvas.create_line(
            l_crop, h - b_crop, l_crop + length, h - b_crop, fill=color, width=width
        )
        self.canvas.create_line(
            l_crop, h - b_crop, l_crop, h - b_crop - length, fill=color, width=width
        )
        self.canvas.create_line(
            w - r_crop,
            h - b_crop,
            w - r_crop - length,
            h - b_crop,
            fill=color,
            width=width,
        )
        self.canvas.create_line(
            w - r_crop,
            h - b_crop,
            w - r_crop,
            h - b_crop - length,
            fill=color,
            width=width,
        )

    def on_monitor_change(self, choice):
        idx = int(choice.split(" ")[1])
        self.app.update_setting("monitor_index", idx)
        ScreenEditor(self.master, self.app)
        self.destroy()

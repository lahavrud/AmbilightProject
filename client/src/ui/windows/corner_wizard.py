import tkinter as tk
import customtkinter as ctk


class CornerWizard(tk.Toplevel):
    def __init__(self, parent, app_controller):
        super().__init__(parent)
        self.app = app_controller

        # --- CustomTkinter Compatibility Patch ---
        self.block_update_dimensions_event = lambda: None
        self.unblock_update_dimensions_event = lambda: None

        # Load existing layout
        layout = self.app.config_mgr.get_nested("client", "layout") or {
            "left": 0,
            "top": 0,
            "right": 0,
            "bottom": 0,
        }

        # CHANGE: Use StringVar instead of IntVar to allow empty strings without errors
        self.sides = {
            "top": tk.StringVar(value=str(layout.get("top", 0))),
            "bottom": tk.StringVar(value=str(layout.get("bottom", 0))),
            "left": tk.StringVar(value=str(layout.get("left", 0))),
            "right": tk.StringVar(value=str(layout.get("right", 0))),
        }

        # Window config
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.0)
        self.configure(bg="black")

        monitor = self.app.grabber.get_monitor_geometry()
        self.geometry(
            f"{monitor['width']}x{monitor['height']}+{monitor['left']}+{monitor['top']}"
        )

        self.canvas = tk.Canvas(self, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self._setup_ui()
        self.bind("<Escape>", lambda e: self.destroy())

        self.update_idletasks()
        self.after(100, self._reveal_window)

    def _reveal_window(self):
        try:
            self.attributes("-alpha", 0.9)
            self.focus_force()
            self._refresh_view()
        except Exception as e:
            print(f"[Corner Wizard] Failed to reveal window: {e}")

    def _setup_ui(self):
        self.controls = ctk.CTkFrame(
            self,
            fg_color="#1a1a1a",
            border_width=2,
            border_color="#333",
            corner_radius=15,
        )
        self.controls.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            self.controls, text="LED Layout Builder", font=("Roboto", 20, "bold")
        ).pack(pady=(15, 5))
        ctk.CTkLabel(
            self.controls,
            text="Match the blue lines to your physical LEDs",
            font=("Roboto", 12),
            text_color="#888",
        ).pack(pady=(0, 15))

        grid = ctk.CTkFrame(self.controls, fg_color="transparent")
        grid.pack(pady=10, padx=20)

        self._add_input(grid, "Top", "top", 0, 1)
        self._add_input(grid, "Left", "left", 1, 0)
        self._add_input(grid, "Right", "right", 1, 2)
        self._add_input(grid, "Bottom", "bottom", 2, 1)

        btn_frame = ctk.CTkFrame(self.controls, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame, text="Cancel", width=100, fg_color="#444", command=self.destroy
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            btn_frame,
            text="Apply Layout",
            width=100,
            fg_color="#27AE60",
            hover_color="#2ECC71",
            command=self._save_and_exit,
        ).pack(side="left", padx=5)

    def _add_input(self, master, label, side, r, c):
        frame = ctk.CTkFrame(master, fg_color="#222", corner_radius=10)
        frame.grid(row=r, column=c, padx=10, pady=10)

        ctk.CTkLabel(
            frame, text=label, font=("Roboto", 11, "bold"), text_color="#555"
        ).pack(pady=(5, 0))

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(padx=10, pady=5)

        ctk.CTkButton(
            inner, text="-", width=25, command=lambda: self._inc(side, -1)
        ).pack(side="left")

        entry = ctk.CTkEntry(
            inner,
            width=50,
            textvariable=self.sides[side],
            justify="center",
            border_width=0,
        )
        entry.pack(side="left", padx=5)

        self.sides[side].trace_add("write", lambda *args: self._refresh_view())

        ctk.CTkButton(
            inner, text="+", width=25, command=lambda: self._inc(side, 1)
        ).pack(side="left")

    def _get_safe_val(self, side):
        """Safely converts StringVar to int, returning 0 if empty or invalid."""
        try:
            val = self.sides[side].get()
            if val == "":
                return 0
            return int(val)
        except (ValueError, TypeError):
            return 0

    def _inc(self, side, delta):
        current = self._get_safe_val(side)
        new_val = max(0, current + delta)
        # Update the StringVar with the new string value
        self.sides[side].set(str(new_val))

    def _refresh_view(self):
        if not self.winfo_exists():
            return
        self.canvas.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w <= 1:
            return

        pad = 50
        colors = {
            "top": "#00AAFF",
            "right": "#E67E22",
            "bottom": "#2ECC71",
            "left": "#E74C3C",
        }

        self._draw_side_line(
            pad, pad, w - pad, pad, self._get_safe_val("top"), colors["top"]
        )
        self._draw_side_line(
            w - pad, pad, w - pad, h - pad, self._get_safe_val("right"), colors["right"]
        )
        self._draw_side_line(
            w - pad,
            h - pad,
            pad,
            h - pad,
            self._get_safe_val("bottom"),
            colors["bottom"],
        )
        self._draw_side_line(
            pad, h - pad, pad, pad, self._get_safe_val("left"), colors["left"]
        )

        self._sync_to_esp()

    def _draw_side_line(self, x1, y1, x2, y2, count, color):
        if count > 0:
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=5)
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            offset = 25
            if y1 == y2:
                my += offset if y1 < 200 else -offset
            else:
                mx += offset if x1 < 200 else -offset

            self.canvas.create_text(
                mx, my, text=f"{count} LEDs", fill=color, font=("Roboto", 12, "bold")
            )

    def _sync_to_esp(self):
        layout_data = {side: self._get_safe_val(side) for side in self.sides}
        try:
            self.app.preview_layout(layout_data)
        except Exception:
            pass

    def _save_and_exit(self):
        try:
            total = 0
            for side in self.sides:
                val = self._get_safe_val(side)
                self.app.config_mgr.config["client"]["layout"][side] = val
                total += val

            self.app.config_mgr.config["hardware"]["num_leds"] = total
            self.app.config_mgr._save_local_config(self.app.config_mgr.config)
            print(f"[Corner Wizard] Layout saved: {total} total LEDs")
            self.destroy()
        except Exception as e:
            print(f"[Corner Wizard] Error saving layout: {e}")

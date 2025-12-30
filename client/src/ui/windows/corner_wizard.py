import tkinter as tk
import customtkinter as ctk


class CornerWizard(tk.Toplevel):
    def __init__(self, parent, app_controller):
        super().__init__(parent)
        self.app = app_controller

        # --- CustomTkinter Compatibility Patch ---
        # Prevents AttributeError when CTK checks for scaling methods in Toplevel
        self.block_update_dimensions_event = lambda: None
        self.unblock_update_dimensions_event = lambda: None

        # Load existing layout from configuration
        layout = self.app.config_mgr.get_nested("client", "layout") or {
            "left": 0,
            "top": 0,
            "right": 0,
            "bottom": 0,
        }
        self.sides = {
            "top": tk.IntVar(value=layout.get("top", 0)),
            "bottom": tk.IntVar(value=layout.get("bottom", 0)),
            "left": tk.IntVar(value=layout.get("left", 0)),
            "right": tk.IntVar(value=layout.get("right", 0)),
        }

        # Window configuration
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        # Start invisible to prevent flicker during initial geometry calculation
        self.attributes("-alpha", 0.0)
        self.configure(bg="black")

        # Set geometry based on current monitor
        monitor = self.app.grabber.get_monitor_geometry()
        self.geometry(
            f"{monitor['width']}x{monitor['height']}+{monitor['left']}+{monitor['top']}"
        )

        self.canvas = tk.Canvas(self, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self._setup_ui()

        # Keyboard bindings
        self.bind("<Escape>", lambda e: self.destroy())

        # Ensure dimensions are calculated before showing the window
        self.update_idletasks()
        self.after(100, self._reveal_window)

    def _reveal_window(self):
        """Gradually reveal window once dimensions are settled."""
        try:
            self.attributes("-alpha", 0.9)
            self.focus_force()
            self._refresh_view()
        except Exception as e:
            print(f"[Corner Wizard] Failed to reveal window: {e}")

    def _setup_ui(self):
        # Central control panel
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

        # Diamond-shaped grid for side inputs
        grid = ctk.CTkFrame(self.controls, fg_color="transparent")
        grid.pack(pady=10, padx=20)

        self._add_input(grid, "Top", "top", 0, 1)
        self._add_input(grid, "Left", "left", 1, 0)
        self._add_input(grid, "Right", "right", 1, 2)
        self._add_input(grid, "Bottom", "bottom", 2, 1)

        # Action buttons
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
        """Helper to add labeled numeric input with +/- buttons."""
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

        # Trigger redraw on any change
        self.sides[side].trace_add("write", lambda *args: self._refresh_view())

        ctk.CTkButton(
            inner, text="+", width=25, command=lambda: self._inc(side, 1)
        ).pack(side="left")

    def _inc(self, side, delta):
        """Increments or decrements the side LED count."""
        try:
            val = self.sides[side].get()
            self.sides[side].set(max(0, val + delta))
        except Exception:
            print(f"[Corner Wizard] Invalid input for {side}, resetting to 0")
            self.sides[side].set(0)

    def _refresh_view(self):
        """Redraws the digital representation and syncs with hardware."""
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

        # Draw the virtual layout lines on canvas
        self._draw_side_line(
            pad, pad, w - pad, pad, self.sides["top"].get(), colors["top"]
        )
        self._draw_side_line(
            w - pad, pad, w - pad, h - pad, self.sides["right"].get(), colors["right"]
        )
        self._draw_side_line(
            w - pad, h - pad, pad, h - pad, self.sides["bottom"].get(), colors["bottom"]
        )
        self._draw_side_line(
            pad, h - pad, pad, pad, self.sides["left"].get(), colors["left"]
        )

        self._sync_to_esp()

    def _draw_side_line(self, x1, y1, x2, y2, count, color):
        """Draws a single side line with an LED count label."""
        if count > 0:
            # Main side line
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=5)

            # LED count label placement
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
        """Sends current layout data to the controller for live preview."""
        layout_data = {side: var.get() for side, var in self.sides.items()}
        try:
            self.app.preview_layout(layout_data)
        except Exception:
            # Silent fail for attribute errors during init
            pass

    def _save_and_exit(self):
        """Saves values to config manager and persists to disk."""
        try:
            for side, var in self.sides.items():
                self.app.config_mgr.config["client"]["layout"][side] = var.get()

            # Update hardware num_leds based on new layout sum
            total = sum(var.get() for var in self.sides.values())
            self.app.config_mgr.config["hardware"]["num_leds"] = total

            self.app.config_mgr._save_local_config(self.app.config_mgr.config)
            print(f"[Corner Wizard] Layout saved: {total} total LEDs")
            self.destroy()
        except Exception as e:
            print(f"[Corner Wizard] Error saving layout: {e}")

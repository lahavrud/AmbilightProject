import tkinter as tk
import customtkinter as ctk


class ScreenEditor(tk.Toplevel):
    def __init__(self, parent, app_controller):
        super().__init__(parent)
        self.app = app_controller

        self.title("Screen Editor")
        self.overrideredirect(True)
        self.configure(bg="black")
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.7)

        monitor = self.app.grabber.get_monitor_geometry()
        geo = (
            f"{monitor['width']}x{monitor['height']}+{monitor['left']}+{monitor['top']}"
        )
        self.geometry(geo)

        self.bind("<Escape>", lambda e: self.destroy())

        self._setup_ui()

        self.after(50, lambda: self.focus_force())

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
            self.controls, text="Screen Area Editor", font=("Roboto", 18, "bold")
        ).pack(pady=(15, 10), padx=20)

        ctk.CTkLabel(self.controls, text="Active Monitor:").pack(pady=(5, 0))

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

        ctk.CTkLabel(
            self.controls,
            text="Adjust crop settings in\nthe main window to see\nchanges here.",
            text_color="gray",
            font=("Arial", 12),
        ).pack(pady=10)

        ctk.CTkButton(
            self.controls,
            text="Done (ESC)",
            command=self.destroy,
            fg_color="#444",
            hover_color="#333",
        ).pack(pady=20, padx=20, fill="x")

    def on_monitor_change(self, choice):
        idx = int(choice.split(" ")[1])
        self.app.update_setting("monitor_index", idx)
        ScreenEditor(self.master, self.app)
        self.destroy()

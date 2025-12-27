import mss
import numpy as np
from PIL import Image


class ScreenGrabber:
    def __init__(self, config_manager):
        self.cfg = config_manager
        self.gamma_table = np.arange(256, dtype=np.uint8)

        self.reload_config()

    def reload_config(self):
        # Creates a gamma values table to save computing time
        gamma_val = self.cfg.get_nested("client", "gamma") or 2
        arr = np.arange(256)
        corrected = ((arr / 255.0) ** gamma_val) * 255
        self.gamma_table = corrected.astype(np.uint8)

        # Saves settings
        self.monitor_idx = self.cfg.get_nested("client", "monitor_index") or 1
        self.depth = self.cfg.get_nested("client", "depth") or 100
        self.leds = self.cfg.get_nested(
            "client", "layout"
        )  # dict: left, top, right, bottom

    def get_monitors_list(self):
        """Returns a list of available monitor indices (e.g. ['Monitor 1', 'Monitor 2'])"""
        with mss.mss() as sct:
            count = len(sct.monitors)
            return [f"Monitor {i}" for i in range(1, count)]

    def get_snapshot(self):
        """Returns a PIL Image for the UI"""
        with mss.mss() as sct:
            if self.monitor_idx >= len(sct.monitors):
                print(f"[Screen] Monitor {self.monitor_idx} not found, using 1")
                self.monitor_idx = 1
            monitor = sct.monitors[self.monitor_idx]
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            return img

    def _process_side(self, img_array, num_leds, is_vertical, reverse=False):
        """Helper function to proccess one side.
        Handles transposing of vertical sides.
        Handles reversing depending on wiring"""
        if num_leds == 0:
            return b""
        if is_vertical:
            img_array = img_array.transpose(1, 0, 2)

        img = Image.fromarray(img_array)

        # Using image resize to get color average of an area
        resized_img = img.resize((num_leds, 1), Image.Resampling.BILINEAR)

        # Back to array and change to gamma values
        color_data = np.array(resized_img)[0]
        corrected_color = self.gamma_table[color_data]

        # reversing (left and bottom)
        if reverse:
            corrected_color = corrected_color[::-1]

        return corrected_color.flatten().tobytes()

    def get_frame_bytes(self):
        """Captures screen, crops roi, calculates average colors per zone, and returns a raw byte"""
        try:
            # Initial sct in the current thread
            with mss.mss() as sct:
                # Monitor availibiliy
                if self.monitor_idx >= len(sct.monitors):
                    print(f"[Screen] Monitor {self.monitor_idx} not found, using 1")
                    self.monitor_idx = 1

                monitor = sct.monitors[self.monitor_idx]

                # Screen grabbing
                sct_img = sct.grab(monitor)

                # Image to array, BRG to RGB
                img = np.array(sct_img)[:, :, :3]
                img = img[:, :, ::-1]

                h, w, _ = img.shape

                # Calculate safe depth (smaller than screen size)
                safe_depth_x = min(self.depth, w // 2)
                safe_depth_y = min(self.depth, h // 2)

                # Slicing sides
                img_left = img[:, :safe_depth_x]
                img_top = img[:safe_depth_y, :]
                img_right = img[:, -safe_depth_x:]
                img_bottom = img[-safe_depth_y:, :]

                # Proccessing
                bytes_left = self._process_side(
                    img_left, self.leds["left"], is_vertical=True, reverse=True
                )
                bytes_top = self._process_side(
                    img_top, self.leds["top"], is_vertical=False, reverse=False
                )
                bytes_right = self._process_side(
                    img_right, self.leds["right"], is_vertical=True, reverse=False
                )
                bytes_bottom = self._process_side(
                    img_bottom, self.leds["bottom"], is_vertical=False, reverse=True
                )

                return bytes_left + bytes_top + bytes_right + bytes_bottom

        except Exception as e:
            print(f"[Screen] Error grabbing frame: {e}")
            return None

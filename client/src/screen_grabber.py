import mss
import numpy as np
from PIL import Image


class ScreenGrabber:
    def __init__(self, config_manager):
        self.cfg = config_manager
        self.gamma_table = np.arange(256, dtype=np.uint8)

        self.phys_monitor = {}
        self.capture_area = {}

        self.reload_config()

    def reload_config(self):
        # 1. Gamma Correction Table
        gamma_val = self.cfg.get_nested("client", "gamma") or 2
        arr = np.arange(256)
        corrected = ((arr / 255.0) ** gamma_val) * 255
        self.gamma_table = corrected.astype(np.uint8)

        # 2. General Settings
        self.monitor_idx = self.cfg.get_nested("client", "monitor_index") or 1
        self.depth = int(self.cfg.get_nested("client", "depth") or 100)
        self.leds = self.cfg.get_nested(
            "client", "layout"
        )  # dict: left, top, right, bottom

        # 3. Cropping Logic
        crops = self.cfg.get_nested("client", "cropping") or {}
        crop_t = crops.get("top", 0)
        crop_b = crops.get("bottom", 0)
        crop_l = crops.get("left", 0)
        crop_r = crops.get("right", 0)

        # 4. Calculate Geometry
        with mss.mss() as sct:
            if self.monitor_idx >= len(sct.monitors):
                self.monitor_idx = 1

            self.phys_monitor = sct.monitors[self.monitor_idx]

            phys_w = self.phys_monitor["width"]
            phys_h = self.phys_monitor["height"]

            new_w = phys_w - crop_l - crop_r
            new_h = phys_h - crop_t - crop_b

            if new_w < 1:
                new_w = 100
            if new_h < 1:
                new_h = 100

            self.capture_area = {
                "top": self.phys_monitor["top"] + crop_t,
                "left": self.phys_monitor["left"] + crop_l,
                "width": new_w,
                "height": new_h,
                "mon": self.monitor_idx,
            }

    def get_monitors_list(self):
        """Returns a list of available monitor indices (e.g. ['Monitor 1', 'Monitor 2'])"""
        with mss.mss() as sct:
            # sct.monitors[0] is "All Monitors"
            count = len(sct.monitors)
            return [f"Monitor {i}" for i in range(1, count)]

    def get_snapshot(self):
        """
        Returns a PIL Image for the UI.
        We capture the FULL physical monitor (self.phys_monitor) so the UI
        can draw the black crop overlays on top of the real image.
        """
        with mss.mss() as sct:
            sct_img = sct.grab(self.phys_monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            return img

    def _process_side(self, img_array, num_leds, is_vertical, reverse=False):
        """
        Helper function to proccess one side.
        Handles transposing of vertical sides.
        Handles reversing depending on wiring.
        """
        if num_leds == 0:
            return b""
        if is_vertical:
            img_array = img_array.transpose(1, 0, 2)

        img = Image.fromarray(img_array)

        # Using image resize to get color average of an area (High Quality Downsampling)
        resized_img = img.resize((num_leds, 1), Image.Resampling.BILINEAR)

        # Back to array and apply gamma correction
        color_data = np.array(resized_img)[0]
        corrected_color = self.gamma_table[color_data]

        # Reversing (needed for standard LED strip wiring usually on Left and Bottom)
        if reverse:
            corrected_color = corrected_color[::-1]

        return corrected_color.flatten().tobytes()

    def get_frame_bytes(self):
        """
        Captures screen (CROPPED area), calculates average colors per zone, and returns raw bytes.
        """
        try:
            with mss.mss() as sct:
                # 1. Capture ONLY the cropped area (Using the pre-calculated capture_area)
                sct_img = sct.grab(self.capture_area)

                # 2. Convert to Numpy (BGRA -> RGB)
                img = np.array(sct_img)[:, :, :3]
                img = img[:, :, ::-1]  # BGR to RGB

                h, w, _ = img.shape

                # 3. Calculate safe depth
                # Depth is taken FROM the crop line inwards.
                safe_depth_x = min(self.depth, w // 2)
                safe_depth_y = min(self.depth, h // 2)

                if safe_depth_x < 1:
                    safe_depth_x = 1
                if safe_depth_y < 1:
                    safe_depth_y = 1

                # 4. Slicing sides based on Depth
                img_left = img[:, :safe_depth_x]
                img_top = img[:safe_depth_y, :]
                img_right = img[:, -safe_depth_x:]
                img_bottom = img[-safe_depth_y:, :]

                # 5. Processing (Using your original logic)
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

    def get_monitor_geometry(self):
        """
        Returns the FULL PHYSICAL geometry.
        Required for the Screen Editor UI to draw the crop overlays correctly.
        """
        return self.phys_monitor

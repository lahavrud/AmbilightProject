import os
import sys
from src.config_manager import ConfigManager

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


def test_default_ConfigManager():
    """
    Ensures config structure is as planned
    """
    cfg = ConfigManager()
    expected_config = {
        "network": {"hostname": "ambilight", "wifi_ssid": "", "wifi_pass": ""},
        "hardware": {
            "baud_rate": 115200,
            "num_leds": 60,
            "brightness": 50,
            "max_milliamps": 1500,
            "smoothing_speed": 20,
        },
        "client": {
            "com_port": "COM3",
            "monitor_index": 1,
            "gamma": 2.2,
            "depth": 100,
            "layout": {"left": 10, "top": 20, "right": 10, "bottom": 20},
        },
    }
    assert cfg.config == expected_config

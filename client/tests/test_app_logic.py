import pytest
from typing import cast
from unittest.mock import patch, MagicMock
from src.models import AppMode
from src.app_controller import AmbilightApp


@pytest.mark.parametrize(
    "mode, kwargs, expected_cmd",
    [
        (AppMode.OFF, {}, {"cmd": "mode", "value": "off"}),
        (AppMode.RAINBOW, {}, {"cmd": "mode", "value": "rainbow"}),
        (AppMode.AMBILIGHT, {}, {"cmd": "mode", "value": "ambilight"}),
        (
            AppMode.STATIC,
            {"color": [0, 0, 255]},
            {"cmd": "mode", "value": "static", "color": [0, 0, 255]},
        ),
    ],
)
@patch("src.app_controller.SerialTransmitter")
def test_set_mode_sends_correct_commands(
    MockSerialTransmitter, mode, kwargs, expected_cmd
):
    """Check if all modes send the right message"""
    # 1. Arrange
    app = AmbilightApp()

    if mode == AppMode.OFF:
        app.current_mode = AppMode.RAINBOW

    mock_instance = cast(MagicMock, app.esp_link)

    # 2. Act
    app.set_mode(mode, **kwargs)

    # 3. Assert
    mock_instance.send_command.assert_called_once_with(expected_cmd)

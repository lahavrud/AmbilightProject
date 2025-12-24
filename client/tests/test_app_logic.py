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
def test_set_static_mode_sends_correct_json(
    MockSerialTransmitter, mode, kwargs, expected_cmd
):
    # 1. Arrange
    app = AmbilightApp()

    # 2. Act
    app.set_mode(AppMode.STATIC, color=[255, 0, 0])

    # 3. Assert
    mock_instance = cast(MagicMock, app.serial_comm)

    expected_cmd = {"cmd": "mode", "value": "static", "color": [255, 0, 0]}

    mock_instance.send_command.assert_called_once_with(expected_cmd)

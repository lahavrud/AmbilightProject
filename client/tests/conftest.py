import sys
from unittest.mock import MagicMock

sys.modules["mss"] = MagicMock()
sys.modules["pystray"] = MagicMock()
sys.modules["PIL"] = MagicMock()
sys.modules["PIL.Image"] = MagicMock()

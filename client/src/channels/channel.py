from abc import ABC, abstractmethod
import json
import time


class Channel(ABC):
    # --- Connection Methods ---
    @abstractmethod
    def connect(self):
        """Initiate connection resource"""
        pass

    @abstractmethod
    def disconnect(self):
        """Close resource and let go of port"""
        pass

    # --- Transmittion Methods ---
    @abstractmethod
    def send_colors(self, color_data):
        """Get pixel data by bytes and send it to LEDs"""
        pass

    @abstractmethod
    def send_command(self, cmd_dict):
        """Get dictionary and send it as a command in JSON format"""
        pass

    # --- Reception Methods ---
    @abstractmethod
    def read_packet(self):
        """Read a single line/packet from the channel"""
        pass

    def wait_for_json(self, timeout=2.0):
        """
        Polls the channel for a valid JSON response within the timeout period.
        """
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            line = self.read_packet()
            if line:
                try:
                    # Attempt to parse as JSON
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue  # Not a JSON, keep looking
            time.sleep(0.01)  # Prevent CPU hogging
        return None

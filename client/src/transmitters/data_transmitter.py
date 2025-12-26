from abc import ABC, abstractmethod


class DataTransmitter(ABC):
    @abstractmethod
    def connect(self):
        """Initiate connection resource"""
        pass

    @abstractmethod
    def send_colors(self, color_data):
        """Get pixel data by bytes and send it to LEDs"""
        pass

    @abstractmethod
    def send_command(self, cmd_dict):
        """Get dictionary and send it as a command in JSON format"""
        pass

    @abstractmethod
    def disconnect(self):
        """Close resource and let go of port"""
        pass

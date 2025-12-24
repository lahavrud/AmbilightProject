import socket
import json
from src.transmitters.data_transmitter import DataTransmitter


class UdpTransmitter(DataTransmitter):
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock = None

        self.connect()

    def connect(self):
        try:
            # AF_INET = IPv4 | SOCK_DGRAM = UDP
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            print(f"[UDP] Resolving IP for {self.host}...")
            self.resolved_ip = socket.gethostbyname(self.host)
            print(f"[UDP] Target resolved: {self.resolved_ip}:{self.port}")
        except socket.gaierror:
            print(f"[UDP Error] Could not resolve hostname: {self.host}")
            self.resolved_ip = None
        except Exception as e:
            print(f"[UDP Error] Initialization failed: {e}")

    def send_command(self, command_dict: dict):
        if not self.sock or not self.resolved_ip:
            return

        try:
            # JSON to bytes
            message = json.dumps(command_dict)
            data = message.encode("utf-8")

            self.sock.sendto(data, (self.resolved_ip, self.port))

        except Exception as e:
            print(f"[UDP Send Error] {e}")

    def send_colors(self, color_data: bytes):
        """Sends raw color data by bytes"""
        if not self.sock or not self.resolved_ip:
            return

        try:
            self.sock.sendto(color_data, (self.resolved_ip, self.port))
        except Exception as e:
            print(f"[UDP Send Error] {e}")

    def disconnect(self):
        if self.sock:
            self.sock.close()
            self.sock = None

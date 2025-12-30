import socket
import json
import select
from src.channels.channel import Channel


class UdpChannel(Channel):
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock = None
        self.resolved_ip = None

        self.connect()

    # --- Connection Methods ---
    def connect(self):
        """Initializes the UDP socket and resolves the target hostname."""
        try:
            # AF_INET = IPv4 | SOCK_DGRAM = UDP
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setblocking(False)

            print(f"[UDP] Resolving IP for {self.host}...")
            self.resolved_ip = socket.gethostbyname(self.host)
            print(f"[UDP] Target resolved: {self.resolved_ip}:{self.port}")
        except socket.gaierror:
            print(f"[UDP Error] Could not resolve hostname: {self.host}")
            self.resolved_ip = None
        except Exception as e:
            print(f"[UDP Error] Initialization failed: {e}")

    def disconnect(self):
        if self.sock:
            self.sock.close()
            self.sock = None
            print("[UDP] Socket closed.")

    # --- Transmittion Methods ---
    def send_command(self, command_dict: dict):
        """
        Sends a JSON command using 'Cmd' protocol.
        Packet foramt: [Cmd] [JSON String] [\n]
        """
        if not self.sock or not self.resolved_ip:
            return

        try:
            json_str = json.dumps(command_dict)
            # Ensure the command protocol matches Serial for consistency
            final_message = f"Cmd{json_str}\n"
            data = final_message.encode("utf-8")

            self.sock.sendto(data, (self.resolved_ip, self.port))
            print(f"[UDP] Sent Commad: {json_str}")

        except Exception as e:
            print(f"[UDP Send Error] {e}")

    def send_colors(self, color_data: bytes):
        """Sends raw color data as bytes directly."""
        if not self.sock or not self.resolved_ip:
            return

        try:
            self.sock.sendto(color_data, (self.resolved_ip, self.port))
        except Exception as e:
            print(f"[UDP Send Error] {e}")

    # --- Reception Methods ---
    def read_packet(self):
        """
        Reads a single packet from the UDP socket.
        Since UDP is packet-based, one 'recvfrom' equals one 'line'.
        """
        if not self.sock:
            return None

        try:
            # Check if there is data waiting in the buffer (1ms timeout)
            # This prevents the program from hanging while waiting for ESP
            ready = select.select([self.sock], [], [], 0.001)
            if ready[0]:
                # 4096 is more than enough for a config JSON
                data, addr = self.sock.recvfrom(4096)
                if data:
                    return data.decode("utf-8").strip()
        except BlockingIOError:
            # No data available in non-blocking mode
            pass
        except Exception as e:
            print(f"[UDP Read Error] {e}")

        return None

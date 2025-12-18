import serial
import time
import struct

class SerialCommunicator:
    def __init__(self, port, baud_rate):
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.is_connected = False
        
        self._connect()

    def _connect(self):
        """Internal method to try opening the port"""
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
                
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
            self.is_connected = True
            print(f"[Serial] Connected to {self.port} @ {self.baud_rate}")
            
            # Waiting On ESP Reset
            time.sleep(2) 
            
        except serial.SerialException as e:
            print(f"[Serial] Connection failed: {e}")
            self.is_connected = False

    def send_colors(self, color_data):
        """
        Gets bytes array that represents color data,
        builds the packet with header,
        handles reconnecting.
        """
        if not self.is_connected:
            # Should add cooldown (?)
            self._connect()
            if not self.is_connected:
                return 

        # Ada Light Protocol
        num_leds = len(color_data) // 3
        if num_leds == 0: return

        count = num_leds - 1
        
        # Split Count to hi-byte and lo-byte
        count_hi = (count >> 8) & 0xFF
        count_lo = count & 0xFF
        
        checksum = count_hi ^ count_lo ^ 0x55
        
        header = struct.pack('>3sBBB', b'Ada', count_hi, count_lo, checksum)
        
        try:
            self.ser.write(header + color_data)
            # Depends on performance could add:
            # time.sleep(0.001) 
        except (serial.SerialException, OSError):
            print("[Serial] Lost connection! Reconnecting...")
            self.is_connected = False
            try:
                self.ser.close()
            except:
                pass

    def close(self):
        if self.ser:
            self.ser.close()
            self.is_connected = False
            print("[Serial] Port closed.")
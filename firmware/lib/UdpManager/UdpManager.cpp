#include "UdpManager.h"

UdpManager::UdpManager(PacketParser& packetParser) : parser(packetParser) {
}

void UdpManager::begin() {
    AppConfig& cfg = AppConfig::get();
    if (udp.begin(cfg.network.udp_port)) {
        Serial.print("UdpManager Ready on port: ");
        Serial.println(cfg.network.udp_port);
    }
    else {
        Serial.println("Error: Failed to start UDP listener");
    }
}

void UdpManager::process() {
    int packetSize = udp.parsePacket();

    if (packetSize > 0) {
        if (packetSize > UDP_BUFFER_SIZE) {
           packetSize = UDP_BUFFER_SIZE;
        }
        int16_t len = udp.read(packetBuffer, packetSize);

        bool isCommand = (packetBuffer[0] == '{') || 
                 (len > 3 && packetBuffer[0] == 'C' && packetBuffer[1] == 'm' && packetBuffer[2] == 'd');
        
        if(isCommand) {
            parser.setResponder(this);
            
            for (int i = 0; i < len; i++) {
                parser.parse(packetBuffer[i]);
            }
        }
        else {
            parser.pushColorBuffer(packetBuffer, len);
        }
    }
}

void UdpManager::sendResponse(const String& response) {
    udp.beginPacket(udp.remoteIP(), udp.remotePort());
    udp.print(response);
    udp.endPacket();
}
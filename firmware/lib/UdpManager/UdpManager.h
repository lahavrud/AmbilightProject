#ifndef UDP_MANAGER_H
#define UDP_MANAGER_H

#include <WiFiUdp.h>
#include <WiFi.h>
#include <Arduino.h>

#include "IInputManager.h"
#include "AppConfig.h"
#include "PacketParser.h"

#define UDP_BUFFER_SIZE 1460

class UdpManager : public IInputManager {
private:
    PacketParser& parser;
    WiFiUDP udp;
    uint8_t packetBuffer[UDP_BUFFER_SIZE];

public:
    UdpManager(PacketParser& PacketParser);

    void begin() override;
    void process() override;

    void debugStatus();
};

#endif
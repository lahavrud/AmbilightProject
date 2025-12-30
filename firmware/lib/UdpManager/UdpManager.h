#ifndef UDP_MANAGER_H
#define UDP_MANAGER_H

#include <WiFiUdp.h>
#include <WiFi.h>
#include <Arduino.h>

#include "IInputManager.h"
#include "IResponder.h"
#include "AppConfig.h"
#include "PacketParser.h"

#define UDP_BUFFER_SIZE 1460

class UdpManager : public IInputManager, public IResponder {
private:
    PacketParser& parser;
    WiFiUDP udp;
    uint8_t packetBuffer[UDP_BUFFER_SIZE];

public:
    UdpManager(PacketParser& PacketParser);

    // InputManager
    void begin() override;
    void process() override;

    // Responder
    void sendResponse(const String& response) override;
};

#endif
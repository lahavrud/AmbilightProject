#include "SerialManager.h"

SerialManager::SerialManager(PacketParser& packetParser) : parser(packetParser) {
}

void SerialManager::begin() {
    AppConfig& cfg = AppConfig::get();
    Serial.begin(cfg.hardware.baud_rate);
    Serial.println("SerialManager Ready (Delegating to PacketParser)");
}

void SerialManager::process() {
    if (Serial.available() > 0) {
        parser.setResponder(this);
        while (Serial.available() > 0) {
            uint8_t c = Serial.read();
            parser.parse(c);
    }
    parser.setResponder(nullptr);
    }
}

void SerialManager::sendResponse(const String& response) {
    Serial.println(response);
}

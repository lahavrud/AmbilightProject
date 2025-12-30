#ifndef SERIAL_MANAGER_H
#define SERIAL_MANAGER_H

#include <Arduino.h>

#include "IInputManager.h"
#include "AppConfig.h"
#include "PacketParser.h"

class SerialManager : public IInputManager, public IResponder {
private:
    PacketParser& parser;

public:
    SerialManager(PacketParser& PacketParser);

    // InputManager
    void begin() override;
    void process() override;

    // Responder
    void sendResponse(const String& response) override;
};

#endif
#ifndef SERIAL_MANAGER_H
#define SERIAL_MANAGER_H

#include <Arduino.h>

#include "IInputManager.h"
#include "AppConfig.h"
#include "PacketParser.h"

class SerialManager : public IInputManager {
private:
    PacketParser& parser;

public:
    SerialManager(PacketParser& PacketParser);

    void begin() override;
    void process() override;
};

#endif
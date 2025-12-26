#ifndef SERIAL_MANAGER_H
#define SERIAL_MANAGER_H

#include <Arduino.h>
#include "PacketParser.h"


class SerialManager {
private:
    PacketParser& parser;

public:
    SerialManager(PacketParser& PacketParser);

    void begin();
    void process();
};

#endif
#ifndef SERIAL_MANAGER_H
#define SERIAL_MANAGER_H

#include <Arduino.h>
#include <ArduinoJson.h>
#include "LedController.h"
#include "AppConfig.h"

#define CMD_BUFFER_SIZE 512

class SerialManager {
private:
    LedController& ledController;

    enum SerialState {
        ST_IDLE,
        
        // Adalight Protocol
        ST_ADA_WAIT_d,
        ST_ADA_WAIT_a,
        ST_ADA_WAIT_HI,
        ST_ADA_WAIT_LO,
        ST_ADA_WAIT_CHK,
        ST_ADA_READ_DATA,

        // Command Protocol
        ST_CMD_WAIT_m,
        ST_CMD_WAIT_d,
        ST_CMD_READ_JSON
    };
    SerialState state;

    uint8_t tempHi, tempLo, tempChk;
    uint16_t dataBytesRead;
    uint16_t currentNumLeds;
    
    char cmdBuffer[CMD_BUFFER_SIZE];
    uint16_t cmdBufferIndex;

    void processAdalight(uint8_t c);
    void processCommand(uint8_t c);

    void executeJsonCommand();

    void handleConfigUpdate(JsonDocument& doc);
    void handleModeChange(JsonDocument& doc);

public:
    SerialManager(LedController& controller);
    
    void begin();
    void process();
};

#endif
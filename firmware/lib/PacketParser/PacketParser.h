#ifndef PACKET_PARSER_H
#define PACKET_PARSER_H

#include <Arduino.h>
#include <ArduinoJson.h>
#include "LedController.h"

#define CMD_BUFFER_SIZE 512

class PacketParser { 
private:
    LedController& ledController;
    enum ParserState {
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
    ParserState state;

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
    PacketParser(LedController& controller);

    void parse(uint8_t byte);
    void pushColorBuffer(uint8_t* buffer, size_t length);

};

#endif
#include "SerialManager.h"

SerialManager::SerialManager(LedController& controller) : ledController(controller) {
    state = ST_IDLE;
    cmdBufferIndex = 0;
}

void SerialManager::begin() {
    AppConfig& cfg = AppConfig::get();

    Serial.begin(cfg.hardware.baud_rate); // או מה שמוגדר ב-Config
    Serial.println("SerialManager Ready (Ada/Cmd)");
    
    currentNumLeds = ledController.getNumLeds();
}

void SerialManager::process() {
    while (Serial.available() > 0) {
        uint8_t c = Serial.read();

        if (state == ST_IDLE) {
            if (c == 'A') state = ST_ADA_WAIT_d;
            else if (c == 'C') state = ST_CMD_WAIT_m;
        } 
        else if (state >= ST_ADA_WAIT_d && state <= ST_ADA_READ_DATA) {
            processAdalight(c);
        }
        else {
            processCommand(c);
        }
    }
}

// Video Processing
void SerialManager::processAdalight(uint8_t c) {
    switch (state) {
        case ST_ADA_WAIT_d: 
            if (c == 'd') state = ST_ADA_WAIT_a; else state = ST_IDLE; 
            break;
        case ST_ADA_WAIT_a: 
            if (c == 'a') state = ST_ADA_WAIT_HI; else state = ST_IDLE; 
            break;
        case ST_ADA_WAIT_HI: 
            tempHi = c; state = ST_ADA_WAIT_LO; 
            break;
        case ST_ADA_WAIT_LO: 
            tempLo = c; state = ST_ADA_WAIT_CHK; 
            break;
        case ST_ADA_WAIT_CHK:
            tempChk = c;
            if ((tempHi ^ tempLo ^ 0x55) == tempChk) {
                dataBytesRead = 0;
                
                currentNumLeds = ledController.getNumLeds();
                
                state = ST_ADA_READ_DATA;
            } else {
                state = ST_IDLE;
            }
            break;

        case ST_ADA_READ_DATA: {
            CRGB* buffer = ledController.getTargetBuffer();
            
            if (buffer == nullptr) {
                state = ST_IDLE;
                return;
            }

            if (dataBytesRead < (currentNumLeds * 3)) {
                ((uint8_t*)buffer)[dataBytesRead++] = c;
            }

            if (dataBytesRead >= (currentNumLeds * 3)) {
                state = ST_IDLE;
            }
            break;
        }            
        default: state = ST_IDLE; break;
    }
}

// Command Processing
void SerialManager::processCommand(uint8_t c) {
    switch (state) {
        case ST_CMD_WAIT_m:
            if (c == 'm') state = ST_CMD_WAIT_d; else state = ST_IDLE;
            break;
        case ST_CMD_WAIT_d:
            if (c == 'd') {
                state = ST_CMD_READ_JSON;
                cmdBufferIndex = 0;
            } else {
                state = ST_IDLE;
            }
            break;
            
        case ST_CMD_READ_JSON:
            if (c == '\n') {
                cmdBuffer[cmdBufferIndex] = '\0';
                executeJsonCommand();
                state = ST_IDLE;
            } 
            else if (cmdBufferIndex < CMD_BUFFER_SIZE - 1) {
                cmdBuffer[cmdBufferIndex++] = (char)c;
            }
            break;
            
        default: state = ST_IDLE; break;
    }
}

void SerialManager::executeJsonCommand() {
    JsonDocument doc;

    DeserializationError error = deserializeJson(doc, cmdBuffer);

    if (error) {
        Serial.print(F("JSON Parse failed: "));
        Serial.println(error.c_str());
        return;
    }

    const char* command = doc["cmd"];

    if (strcmp(command, "config") == 0) {
        handleConfigUpdate(doc);
    }
    else if (strcmp(command, "mode") == 0) {
        handleModeChange(doc);
    }
    else {
        Serial.println(F("Unknown command"));
    }
}

void SerialManager::handleConfigUpdate(JsonDocument& doc) {
    AppConfig& cfg = AppConfig::get();
    bool changed = false;

    if (doc["num_leds"]) {
        cfg.hardware.num_leds = doc["num_leds"];
        changed = true;
    }

    if (doc["color_order"]) {
        const char* order = doc["color_order"];
        strlcpy(cfg.hardware.color_order, order, sizeof(cfg.hardware.color_order));
        changed = true;
    }

    if (changed) {
        cfg.saveConfig();
        ledController.reloadConfig();
        currentNumLeds = ledController.getNumLeds();
    }
}

void SerialManager::handleModeChange(JsonDocument& doc) {
    const char* modeStr = doc["value"];
    
    if (strcmp(modeStr, "ambilight") == 0) {
        ledController.setMode(MODE_AMBILIGHT);
    }
    else if (strcmp(modeStr, "rainbow") == 0) {
        ledController.setMode(MODE_RAINBOW);
    }
    else if (strcmp(modeStr, "static") == 0) {
        ledController.setMode(MODE_STATIC);
        if (doc["color"]) {
            JsonArray color = doc["color"];
            ledController.setStaticColor(color[0], color[1], color[2]);
        }
    }
    else if (strcmp(modeStr, "off") == 0) {
        ledController.setMode(MODE_OFF);
    }
    
    Serial.print(F("Mode changed to: "));
    Serial.println(modeStr);
}

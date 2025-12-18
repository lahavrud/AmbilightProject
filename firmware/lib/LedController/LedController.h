#ifndef LED_CONTROLLER_H
#define LED_CONTROLLER_H

#include <FastLED.h>
#include "AppConfig.h"

// Will be passed by AppConfig once i figure it out
#define LED_PIN     16
#define LED_TYPE    WS2812B
#define COLOR_ORDER GRB

enum SystemMode {
    MODE_STATIC,
    MODE_RAINBOW,
    MODE_AMBILIGHT,
    MODE_OFF
};

class LedController {
private:
    CRGB* leds = nullptr;
    CRGB* targetLeds = nullptr;

    uint16_t numLeds;

    SystemMode currentMode;
    uint8_t rainbowHue;
    unsigned long lastUpdate; 

    enum SerialState { 
        ST_WAIT_A, ST_WAIT_d, ST_WAIT_a, 
        ST_WAIT_HI, ST_WAIT_LO, ST_WAIT_CHK, 
        ST_READ_DATA 
    };
    SerialState serialState;
    uint8_t tempHi, tempLo, tempChk;
    uint16_t dataBytesRead; // counter for incoming already read bytes 

    // Helper functions
    void processSerial();
    void runRainbow();
    void smoothLeds();
    void allocateMemory(uint16_t count);

public:
    LedController();
    ~LedController();
    
    void begin();
    void update(); 
    
    // API's
    void setMode(SystemMode mode);
    void setStaticColor(int r, int g, int b);
    void setBrightness(int brightness);
};

#endif
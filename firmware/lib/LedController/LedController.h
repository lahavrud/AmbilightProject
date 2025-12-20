#ifndef LED_CONTROLLER_H
#define LED_CONTROLLER_H

#include <FastLED.h>
#include "AppConfig.h"

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
    CRGB staticColor;
    uint8_t rainbowHue;

    // Helper functions
    void runRainbow();
    void smoothLeds();
    void allocateMemory(uint16_t count); // for dynamic led number

public:
    LedController();
    ~LedController();

    void begin();
    void update(); 
    
    // API's
    CRGB* getTargetBuffer();
    uint16_t getNumLeds();

    SystemMode getMode();
    uint8_t getBrightness();
    CRGB getStaticColor();

    void setMode(SystemMode mode);
    void setStaticColor(int r, int g, int b);
    void setBrightness(int brightness);

    void reloadConfig();
};

#endif
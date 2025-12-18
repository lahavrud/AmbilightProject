#include "LedController.h"

LedController::LedController() {
    currentMode = MODE_STATIC;
    rainbowHue = 0;
    serialState = ST_WAIT_A;
    dataBytesRead = 0;
    
    leds = nullptr;
    targetLeds = nullptr;
    numLeds = 0;
}

LedController::~LedController() {
    if (leds) {
        delete [] leds;
        leds = nullptr;
    }
    if (targetLeds) {
        delete [] targetLeds;
        targetLeds = nullptr;
    }
}

void LedController::allocateMemory(uint16_t count) {
    if (leds) delete[] leds;
    if (targetLeds) delete[] targetLeds;

    numLeds = count;

    leds = new CRGB[numLeds];
    targetLeds = new CRGB[numLeds];

    fill_solid(leds, numLeds, CRGB::Black);
    fill_solid(targetLeds, numLeds, CRGB::Black);
}

void LedController::begin() {
    AppConfig& cfg = AppConfig::get();
    
    allocateMemory(cfg.hardware.num_leds);

    // Initiating FastLED
    FastLED.setCorrection(TypicalLEDStrip);
    FastLED.setBrightness(cfg.hardware.brightness);
    FastLED.setMaxPowerInVoltsAndMilliamps(5, cfg.hardware.max_milliamps);

    String order = String(cfg.hardware.color_order);
    order.toUpperCase();
    if (order == "RGB") {
        FastLED.addLeds<LED_TYPE, LED_PIN, RGB>(leds, numLeds);
        Serial.println("Leds init: RGB");
    }
    else if (order == "BRG") {
        FastLED.addLeds<LED_TYPE, LED_PIN, BRG>(leds, numLeds);
        Serial.println("Leds init: BRG");
    }
    else {
        FastLED.addLeds<LED_TYPE, LED_PIN, GRB>(leds, numLeds);
        Serial.println("Leds init: GRB");
    }
    FastLED.show();
}

void LedController::update() {
    if (currentMode == MODE_AMBILIGHT) {
        processSerial();
    } 
    else if (currentMode == MODE_RAINBOW) {
        runRainbow();
    }

    smoothLeds();
    FastLED.show();
}

// State-Machine
void LedController::processSerial() {
    AppConfig& cfg = AppConfig::get();
    
    while (Serial.available() > 0) {
        uint8_t c = Serial.read();

        switch (serialState) {
            case ST_WAIT_A:
                if (c == 'A') serialState = ST_WAIT_d;
                break;
            
            case ST_WAIT_d:
                if (c == 'd') serialState = ST_WAIT_a;
                else serialState = ST_WAIT_A; // טעות, חוזרים להתחלה
                break;

            case ST_WAIT_a:
                if (c == 'a') serialState = ST_WAIT_HI;
                else serialState = ST_WAIT_A;
                break;

            case ST_WAIT_HI:
                tempHi = c;
                serialState = ST_WAIT_LO;
                break;

            case ST_WAIT_LO:
                tempLo = c;
                serialState = ST_WAIT_CHK;
                break;

            case ST_WAIT_CHK:
                tempChk = c;
                // checksum
                if ((tempHi ^ tempLo ^ 0x55) == tempChk) {
                    dataBytesRead = 0;
                    serialState = ST_READ_DATA;
                } else {
                    serialState = ST_WAIT_A;
                }
                break;

            case ST_READ_DATA:
                uint8_t* rawData = (uint8_t*)targetLeds;
                
                if (dataBytesRead < (numLeds * 3)) {
                    rawData[dataBytesRead++] = c;
                }

                if (dataBytesRead >= (numLeds * 3)) {
                    serialState = ST_WAIT_A; 
                }
                break;
        }
    }
}

void LedController::smoothLeds() {
    AppConfig& cfg = AppConfig::get();
    
    if (currentMode == MODE_AMBILIGHT) {
        for (int i = 0; i < numLeds; i++) {
            nblend(leds[i], targetLeds[i], cfg.hardware.smoothing_speed);
        }
    } else {
        // Smart Blend Logic
    }
}

void LedController::runRainbow() {
    AppConfig& cfg = AppConfig::get();
    EVERY_N_MILLISECONDS(20) {
        rainbowHue++;
        fill_rainbow(leds, cfg.hardware.num_leds, rainbowHue, 7);
    }
}

// Control Functions

void LedController::setMode(SystemMode mode) {
    currentMode = mode;
    if (mode == MODE_OFF) {
        fill_solid(leds, numLeds, CRGB::Black);
        fill_solid(targetLeds, numLeds, CRGB::Black);
    }
}

void LedController::setStaticColor(int r, int g, int b) {
    currentMode = MODE_STATIC;
    fill_solid(leds, numLeds, CRGB(r, g, b));
    fill_solid(targetLeds, numLeds, CRGB(r, g, b)); 
}

void LedController::setBrightness(int brightness) {
    FastLED.setBrightness(brightness);
}
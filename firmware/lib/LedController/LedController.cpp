#include "LedController.h"

LedController::LedController() {
    currentMode = MODE_STATIC;
    rainbowHue = 0;
    serialState = ST_WAIT_A;
    dataBytesRead = 0;
}

void LedController::begin() {
    AppConfig& cfg = AppConfig::get();
    
    // Initiating FastLED
    FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, MAX_LEDS);
    FastLED.setCorrection(TypicalLEDStrip);
    FastLED.setBrightness(cfg.brightness);
    FastLED.setMaxPowerInVoltsAndMilliamps(5, cfg.max_milliamps);
     
    fill_solid(leds, MAX_LEDS, CRGB::Black);
    fill_solid(targetLeds, MAX_LEDS, CRGB::Black);
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
    
    // כל עוד יש מידע בבאפר, נקרא אותו אחד-אחד
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
                
                if (dataBytesRead < (cfg.num_leds * 3)) {
                    rawData[dataBytesRead++] = c;
                }

                if (dataBytesRead >= (cfg.num_leds * 3)) {
                    serialState = ST_WAIT_A; 
                }
                break;
        }
    }
}

void LedController::smoothLeds() {
    AppConfig& cfg = AppConfig::get();
    
    if (currentMode == MODE_AMBILIGHT) {
        for (int i = 0; i < cfg.num_leds; i++) {
            nblend(leds[i], targetLeds[i], cfg.smoothing_speed);
        }
    } else {
        // Smart Blend Logic
    }
}

void LedController::runRainbow() {
    AppConfig& cfg = AppConfig::get();
    EVERY_N_MILLISECONDS(20) {
        rainbowHue++;
        fill_rainbow(leds, cfg.num_leds, rainbowHue, 7);
    }
}

// Control Functions

void LedController::setMode(SystemMode mode) {
    currentMode = mode;
    if (mode == MODE_OFF) {
        fill_solid(leds, MAX_LEDS, CRGB::Black);
        fill_solid(targetLeds, MAX_LEDS, CRGB::Black);
    }
}

void LedController::setStaticColor(int r, int g, int b) {
    currentMode = MODE_STATIC;
    fill_solid(leds, AppConfig::get().num_leds, CRGB(r, g, b));
    fill_solid(targetLeds, AppConfig::get().num_leds, CRGB(r, g, b)); 
}

void LedController::setBrightness(int brightness) {
    FastLED.setBrightness(brightness);
}
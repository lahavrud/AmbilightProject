#include "LedController.h"

LedController::LedController() {
    currentMode = MODE_STATIC;
    staticColor = CRGB::Red;
    rainbowHue = 0;
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
    if (currentMode == MODE_RAINBOW) {
        runRainbow();
    }

    smoothLeds();
    FastLED.show();
}

CRGB* LedController::getTargetBuffer() {
    return targetLeds;
}

uint16_t LedController::getNumLeds() {
    return numLeds;
}

void LedController::reloadConfig() {
    begin();
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

// Get Functions
SystemMode LedController::getMode() {
    return currentMode;
}

uint8_t LedController::getBrightness() {
    return FastLED.getBrightness();
}

CRGB LedController::getStaticColor() {
    return staticColor;
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
    CRGB currentStaticColor = CRGB(r, g, b);
    currentMode = MODE_STATIC;
    fill_solid(leds, numLeds, currentStaticColor);
    fill_solid(targetLeds, numLeds, currentStaticColor); 
    staticColor = currentStaticColor;
    FastLED.show();
}

void LedController::setBrightness(int brightness) {
    FastLED.setBrightness(brightness);
}
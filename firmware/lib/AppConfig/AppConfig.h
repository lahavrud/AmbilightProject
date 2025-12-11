#ifndef APP_CONFIG_H
#define APP_CONFIG_H

#include <Arduino.h>

struct Config {
    // Network
    char hostname[32];
    char wifi_ssid[32];
    char wifi_pass[64];

    // Hardware
    uint32_t baud_rate;
    uint16_t num_leds;
    uint8_t brightness;
};

extern Config appConfig;

void loadConfig();

#endif
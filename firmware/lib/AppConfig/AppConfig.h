#ifndef APP_CONFIG_H
#define APP_CONFIG_H

#include <Arduino.h>

class AppConfig {
public:
    static AppConfig& get();

    void loadConfig();

    // Network
    char hostname[32];
    char wifi_ssid[32];
    char wifi_pass[64];

    // Hardware
    uint32_t baud_rate;
    uint16_t num_leds;
    uint8_t brightness;
    uint16_t max_milliamps;
    uint8_t smoothing_speed;

private:
    AppConfig();
    AppConfig(const AppConfig&) = delete;
    void operator=(const AppConfig&) = delete;
};

#endif
#ifndef APP_CONFIG_H
#define APP_CONFIG_H

#include <Arduino.h>
#include <ArduinoJson.h>

// Config Data Structures
struct NetworkConfig {
    char hostname[32] = "ambilight";
    char wifi_ssid[32] = "";
    char wifi_pass[64] = "";
    uint16_t udp_port = 8888;
};

struct HardwareConfig {
    uint32_t baud_rate = 115200;
    uint16_t num_leds = 60;
    uint8_t brightness = 50;
    uint16_t max_milliamps = 1500;
    uint8_t smoothing_speed = 20;
    char color_order[4] = "GRB";
};

struct LedLayout {
    int left = 10;
    int top = 20;
    int right = 10;
    int bottom = 20;
};

struct CropConfig {
    int left = 0;
    int top = 0;
    int right = 0;
    int bottom = 0;
};

struct ClientConfig {
    String com_port = "COM3";
    int monitor_index = 1;
    float gamma = 2.2;
    int depth = 100;
    LedLayout layout;
    CropConfig cropping;
};
class AppConfig {
public:
    static AppConfig& get();

    void loadConfig();
    void saveConfig();
    String getConfigJson();

    NetworkConfig network;
    HardwareConfig hardware;
    ClientConfig client;

private:
    AppConfig() {};
    AppConfig(const AppConfig&) = delete;
    void operator=(const AppConfig&) = delete;
};

#endif
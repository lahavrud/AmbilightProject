#include "AppConfig.h"
#include <LittleFS.h>

AppConfig& AppConfig::get() {
    static AppConfig instance;
    return instance;
}

// ==========================================
// ARDUINOJSON CONVERTERS
// ==========================================

// --- Network ---
void convertToJson(const NetworkConfig& src, JsonVariant dst) {
    dst["hostname"] = src.hostname;
    dst["wifi_ssid"] = src.wifi_ssid;
}
void convertFromJson(JsonVariantConst src, NetworkConfig& dst) {
    if (src["hostname"]) strlcpy(dst.hostname, src["hostname"], sizeof(dst.hostname));
    if (src["wifi_ssid"]) strlcpy(dst.wifi_ssid, src["wifi_ssid"], sizeof(dst.wifi_ssid));
    if (src["wifi_pass"]) strlcpy(dst.wifi_pass, src["wifi_pass"], sizeof(dst.wifi_pass));
}

// --- Hardware ---
void convertToJson(const HardwareConfig& src, JsonVariant dst) {
    dst["baud_rate"] = src.baud_rate;
    dst["num_leds"] = src.num_leds;
    dst["brightness"] = src.brightness;
    dst["max_milliamps"] = src.max_milliamps;
    dst["smoothing_speed"] = src.smoothing_speed;
    dst["color_order"] = src.color_order;
}
void convertFromJson(JsonVariantConst src, HardwareConfig& dst) {
    dst.baud_rate = src["baud_rate"] | 115200;
    dst.num_leds = src["num_leds"] | 60;
    dst.brightness = src["brightness"] | 50;
    dst.max_milliamps = src["max_milliamps"] | 1500;
    dst.smoothing_speed = src["smoothing_speed"] | 20;
    if (src["color_order"]) {
        strlcpy(dst.color_order, src["color_order"], sizeof(dst.color_order));
    }
}

// --- LedLayout ---
void convertToJson(const LedLayout& src, JsonVariant dst) {
    dst["left"] = src.left;
    dst["top"] = src.top;
    dst["right"] = src.right;
    dst["bottom"] = src.bottom;
}
void convertFromJson(JsonVariantConst src, LedLayout& dst) {
    dst.left = src["left"] | 10;
    dst.top = src["top"] | 20;
    dst.right = src["right"] | 10;
    dst.bottom = src["bottom"] | 20;
}

// --- Client ---
void convertToJson(const ClientConfig& src, JsonVariant dst) {
    dst["com_port"] = src.com_port;
    dst["monitor_index"] = src.monitor_index;
    dst["gamma"] = src.gamma;
    dst["depth"] = src.depth;
    dst["layout"] = src.layout; 
}
void convertFromJson(JsonVariantConst src, ClientConfig& dst) {
    dst.com_port = src["com_port"] | "COM3";
    dst.monitor_index = src["monitor_index"] | 1;
    dst.gamma = src["gamma"] | 2.2;
    dst.depth = src["depth"] | 100;
    if (src["layout"]) {
        dst.layout = src["layout"];
    }
}

// ==========================================
// AppConfig Methods
// ==========================================

void AppConfig::loadConfig() {
    if (!LittleFS.begin()) {
        Serial.println("Failed to mount file system");
        return;
    }

    if (!LittleFS.exists("/config.json")) {
        Serial.println("No config file found, creating defaults...");
        saveConfig();
        return;
    }

    File file = LittleFS.open("/config.json", "r");
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, file);
    file.close();

    if (error) {
        Serial.println("Failed to parse config file");
        return;
    }

    if (doc["network"]) network = doc["network"];
    if (doc["hardware"]) hardware = doc["hardware"];
    if (doc["client"]) client = doc["client"];

    Serial.println("Config loaded successfully via converters");
}

void AppConfig::saveConfig() {
    if (!LittleFS.begin()) return;

    JsonDocument doc;
    doc["network"] = network;
    doc["hardware"] = hardware;
    doc["client"] = client;
    
    doc["network"]["wifi_pass"] = network.wifi_pass;

    File file = LittleFS.open("/config.json", "w");
    if (serializeJson(doc, file) == 0) {
        Serial.println("Failed to write config file");
    } else {
        Serial.println("Config saved");
    }
    file.close();
}

String AppConfig::getConfigJson() {
    JsonDocument doc;
    doc["network"] = network;
    doc["hardware"] = hardware;
    doc["client"] = client;
    
    String output;
    serializeJson(doc, output);
    return output;
}
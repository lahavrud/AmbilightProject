#include "AppConfig.h"
#include <ArduinoJson.h>
#include <LittleFS.h>

AppConfig& AppConfig::get() {
    static AppConfig instance;
    return instance;
};

// Defaults
AppConfig::AppConfig() {
    // Network
    strlcpy(hostname, "ambilight", sizeof(hostname));
    wifi_ssid[0] = '\0';
    wifi_pass[0] = '\0';

    // Hardware
    baud_rate = 115200;
    num_leds = 60;
    brightness = 50;
    max_milliamps = 1500;
    smoothing_speed = 20;
}

void AppConfig::loadConfig() {
    if (!LittleFS.begin()) {
        Serial.println("Failed to mount file system");
        return;
    }

    File file = LittleFS.open("/config.json", "r");
    if (!file) {
        Serial.println("No config file found, using defaults");
        return;
    }

    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, file);

    if (error) {
        Serial.println("Failed to parse config file");
        Serial.println(error.c_str());
        file.close();
        return;
    }

    /// Network
    if (doc["network"]["hostname"]) strlcpy(hostname, doc["network"]["hostname"], sizeof(hostname));
    if (doc["network"]["wifi_ssid"]) strlcpy(wifi_ssid, doc["network"]["wifi_ssid"], sizeof(wifi_ssid));
    if (doc["network"]["wifi_pass"]) strlcpy(wifi_pass, doc["network"]["wifi_pass"], sizeof(wifi_pass));

    // Hardware
    baud_rate = doc["hardware"]["baud_rate"] | baud_rate;
    num_leds = doc["hardware"]["num_leds"] | num_leds;
    brightness = doc["hardware"]["brightness"] | brightness;
    max_milliamps = doc["hardware"]["max_milliamps"] | max_milliamps;
    smoothing_speed = doc["hardware"]["max_milliamps"] | smoothing_speed;

    file.close();
    Serial.println("Config loaded successfully");
}

String AppConfig::getConfigJson() {
    JsonDocument doc;
    doc["num_leds"] = num_leds;
    doc["brightness"] = brightness;
    doc["max_milliamps"] = max_milliamps;
    doc["baud_rate"] = baud_rate;
    doc["wifi_ssid"] = wifi_ssid;
    doc["hostname"] = hostname;
    
    String output;
    serializeJson(doc, output);

    return output; 
}
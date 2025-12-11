#include "AppConfig.h"
#include <ArduinoJson.h>
#include <LittleFS.h>

Config appConfig = {
    "ambilight", "", "",
    921600, 60, 50
};

void loadConfig() {
    File file = LittleFS.open("/config.json", "r");
    if (!file) {
        Serial.println("No config file found, using defaults");
        return;
    }
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, file);

    if (error) {
        Serial.println("Failed to parse config file");
        return;
    }

    /// WiFi
    if (doc["network"]["hostname"]) strlcpy(appConfig.hostname, doc["network"]["hostname"], sizeof(appConfig.hostname));
    if (doc["network"]["wifi_ssid"]) strlcpy(appConfig.wifi_ssid, doc["network"]["wifi_ssid"], sizeof(appConfig.wifi_ssid));
    if (doc["network"]["wifi_pass"]) strlcpy(appConfig.wifi_pass, doc["network"]["wifi_pass"], sizeof(appConfig.wifi_pass));

    // Hardware
    appConfig.baud_rate = doc["hardware"]["baud_rate"] | appConfig.baud_rate;
    appConfig.num_leds = doc["hardware"]["num_leds"] | appConfig.num_leds;
    appConfig.brightness = doc["hardware"]["brightness"] | appConfig.brightness;

    file.close();
    Serial.println("Config loaded successfully");
}

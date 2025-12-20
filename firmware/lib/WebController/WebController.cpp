#include "AppConfig.h"
#include "WebController.h"
#include "LedController.h"
#include <WiFi.h>
#include <ESPmDNS.h>
#include <LittleFS.h>
#include <Arduino.h>

WebController::WebController(LedController& ledCtrl) :
    server(80), leds(ledCtrl) {
}

void WebController::begin() {
    AppConfig& cfg = AppConfig::get();

    if (!LittleFS.begin()) {
        Serial.println("LittleFS Mount Failed");
    }

    // WiFi Initiate
    WiFi.mode(WIFI_STA);
    WiFi.setSleep(false);
    WiFi.begin(cfg.network.wifi_ssid, cfg.network.wifi_pass);

    Serial.print("Connecting to WiFi: ");
    Serial.println(cfg.network.wifi_ssid);

    uint8_t retries = 0;
    while (WiFi.status() != WL_CONNECTED && retries < 20) { 
    delay(500);
    Serial.print("."); 
    retries++;
    }

    if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi Connected: " + WiFi.localIP().toString());
    } else {
    Serial.println("\nWiFi Connection Failed!");
    }

    // DNS
    if (MDNS.begin(cfg.network.hostname)) {
    Serial.println("mDNS started: http://" + String(cfg.network.hostname) + ".local");
    }

    // Routes
    server.on("/", [this](){ handleRoot(); });
    server.on("/config", HTTP_GET, [this](){ handleGetConfig(); });
    server.on("/set", [this](){ handleSetColor(); });
    server.on("/brightness", [this](){ handleSetBrightness(); });
    server.on("/mode", [this](){ handleSetMode(); });
    server.on("/get-status", HTTP_GET, [this](){ handleGetStatus(); });
    server.onNotFound([this](){ handleNotFound(); });
    server.begin();
}

// --- Handlers ---
void WebController::handleRoot() {
    if (!LittleFS.begin()) {
        Serial.println("LittleFS failed!");
        return;
    }
    File file = LittleFS.open("/index.html", "r");
    if (!file) {
        server.send(500, "text/plain", "Index missing");
        return;
    }
    server.streamFile(file, "text/html");
    file.close();
}

void WebController::handleGetConfig() {
    String jsonResponse = AppConfig::get().getConfigJson();
    server.send(200, "application/json", jsonResponse);
}

void WebController::handleGetStatus() {
    JsonDocument doc;

    SystemMode currentMode = leds.getMode();
    
    String modeStr = "off";
    if (currentMode == MODE_AMBILIGHT) modeStr = "ambilight";
    else if (currentMode == MODE_RAINBOW) modeStr = "rainbow";
    else if (currentMode == MODE_STATIC) modeStr = "static";

    doc["mode"] = modeStr;
    
    String response;
    serializeJson(doc, response);
    server.send(200, "application/json", response);
}

void WebController::handleSetColor() {
    if (server.hasArg("r") && server.hasArg("g") && server.hasArg("b")) {
        int r = server.arg("r").toInt();
        int g = server.arg("g").toInt();
        int b = server.arg("b").toInt();

        leds.setStaticColor(r, g, b);

        Serial.printf("Set Color: %d,%d,%d\n", r, g, b);
        server.send(200, "text/plain", "OK");
    } else {
        server.send(400, "text/plain", "Missing RGB");
    }
}

void WebController::handleSetBrightness() {
    if (server.hasArg("val")) {
        int val = server.arg("val").toInt();

        leds.setBrightness(val);
        AppConfig::get().hardware.brightness = val;
        Serial.printf("Set Brightness: %d", val);
        server.send(200, "text/plain", "OK");
    } else {
        server.send(400, "text/plain", "Missing val");
    }
}

void WebController::handleSetMode() {
    if (server.hasArg("m")) {
        String m = server.arg("m");
        
        if (m == "static") leds.setMode(MODE_STATIC);
        else if (m == "rainbow") leds.setMode(MODE_RAINBOW);
        else if (m == "ambilight") leds.setMode(MODE_AMBILIGHT);
        else if (m == "off") leds.setMode(MODE_OFF);

        server.send(200, "text/plain", "OK");
    } else {
        server.send(400, "text/plain", "Missing mode");
    }
}

void WebController::handleNotFound() {
    server.send(404, "text/plain", "Not found");
}

void WebController::handleClient() {
    server.handleClient();
}



#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <FastLED.h>
#include <ESPmDNS.h>
#include <LittleFS.h> 
#include "AppConfig.h"

// --- Hardware Settings ---
#define LED_PIN     16
#define MAX_LEDS    800
#define LED_TYPE    WS2812B
#define COLOR_ORDER GRB 

uint8_t hue = 0;

enum SystemMode {
  MODE_STATIC,
  MODE_RAINBOW,
  MODE_AMBILIGHT,
  MODE_OFF
};
enum SystemMode currentMode = MODE_STATIC;

CRGB leds[MAX_LEDS];
CRGB targetLeds[MAX_LEDS];

uint8_t SMOOTHING_SPEED = 30;

WebServer server(80);

// --- Helper Functions ---
void ledsSetup(uint16_t numLeds, uint8_t brightness) {
  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, numLeds);

  FastLED.setCorrection(TypicalLEDStrip); 
  FastLED.setBrightness(brightness);

  FastLED.clear();
  FastLED.show();
}

void runRainbow(uint16_t numLeds) {
  EVERY_N_MILLISECONDS(20) {
    hue++;
    fill_rainbow(leds, numLeds, hue, 7);
    FastLED.show();
  }
}

void runAmbilight(uint16_t numLeds) {
  if (Serial.available() < 6) return;
  if (Serial.read() != 'A') return; 
  if (Serial.read() != 'd') return; 
  if (Serial.read() != 'a') return; 

  unsigned char hibyte = Serial.read(); // Hi-Byte count
  unsigned char lobyte = Serial.read(); // Lo-Byte count
  unsigned char checksum = Serial.read(); // Checksum
  unsigned char result = hibyte ^ lobyte ^ 0x55; 
  if (result != checksum) return;

  Serial.readBytes((char*)targetLeds, numLeds * 3);
}

// --- Handlers ---

// Root Path
void handleRoot() {
  File file = LittleFS.open("/index.html", "r");
  if (!file) {
    server.send(500, "text/plain", "Error: index.html missing!");
    return;
  }
  server.streamFile(file, "text/html");
  file.close();
}

void handleSetColor() {
  if (!server.hasArg("r") || !server.hasArg("g") || !server.hasArg("b")) {
    server.send(400, "text/plain", "Missing args");
    return;
  }

  int r = server.arg("r").toInt();
  int g = server.arg("g").toInt();
  int b = server.arg("b").toInt();

  currentMode = MODE_STATIC;

  fill_solid(leds, appConfig.num_leds, CRGB(r, g, b));
  FastLED.show();

  server.send(200, "text/plain", "OK");
}

void handleSetBrightness() {
  if (!server.hasArg("val")) {
    server.send(400, "text/plain", "Missing args");
    return;
  }
  int val = server.arg("val").toInt();
  FastLED.setBrightness(val);
  FastLED.show();

  server.send(200, "text/plain", "OK");
}
 
void handleSetMode() {
  if (!server.hasArg("m")) {
    server.send(400, "text/plain", "Missing args");
    return;
  }
  String m = server.arg("m");
  if (m == "static") {
    currentMode = MODE_STATIC;
  }
  else if (m == "rainbow") {
    currentMode = MODE_RAINBOW;
  }
  else if(m == "ambilight") {
    currentMode = MODE_AMBILIGHT;
    delay(100);
  }
  else if (m == "off") {
    currentMode = MODE_OFF;
    FastLED.clear();
    FastLED.show();
  }
  server.send(200, "text/plain", "OK");
}

void handleNotFound() {
  server.send(404, "text/plain", "Not found");
}


// --- Setup ---

void setup() {
  Serial.setRxBufferSize(1024);
  Serial.begin(921600); 
  Serial.setTimeout(50);

  if (!LittleFS.begin()) {
    Serial.println("LittleFS Mount Failed. Formatting...");
    LittleFS.format();
    LittleFS.begin();
  } else {
    Serial.println("LittleFS Mounted Successfully");
  }

  loadConfig();

  if (appConfig.baud_rate != 115200) {
    Serial.flush();
    Serial.updateBaudRate(appConfig.baud_rate);
  }

  ledsSetup(appConfig.num_leds, appConfig.brightness);

  // WiFi Initiate
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(appConfig.wifi_ssid, appConfig.wifi_pass);

  Serial.print("Connecting to WiFi: ");
  Serial.println(appConfig.wifi_ssid);

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
  
  if (MDNS.begin(appConfig.hostname)) {
    Serial.println("mDNS started: http://" + String(appConfig.hostname) + ".local");
  }

  server.on("/", handleRoot);
  server.on("/set", handleSetColor);
  server.on("/brightness", handleSetBrightness);
  server.on("/mode", handleSetMode);
  server.onNotFound(handleNotFound);

  server.begin();
}


void loop() {
  if (currentMode == MODE_AMBILIGHT) {
    runAmbilight(appConfig.num_leds);

    for (int i = 0; i < appConfig.num_leds; i++)
    {
      nblend(leds[i], targetLeds[i], SMOOTHING_SPEED);
    }
    FastLED.show();

    static unsigned long lastWifiCheck = 0;
    if (millis()-lastWifiCheck > 500) {
      server.handleClient();
      lastWifiCheck = millis();
    }
  }
  else {
    server.handleClient();
    switch (currentMode) {
      case MODE_STATIC:
        break;
      case MODE_RAINBOW:
        runRainbow(appConfig.num_leds);
        break;
      case MODE_OFF:
        break;
    }
  delay(2);
  }

}
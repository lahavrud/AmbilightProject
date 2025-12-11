#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <FastLED.h>
#include <ESPmDNS.h>
#include <LittleFS.h> 
#include "secrets.h"

// --- Hardware Settings ---
#define LED_PIN     16
#define NUM_LEDS    124
#define BRIGHTNESS  50
#define LED_TYPE    WS2812B
#define COLOR_ORDER GRB 
uint8_t hue = 0;

// --- WiFi Settings ---
const char* ssid = WIFI_SSID;
const char* password = WIFI_PASS;
const char* hostName = HOST_NAME;

enum SystemMode {
  MODE_STATIC,
  MODE_RAINBOW,
  MODE_AMBILIGHT,
  MODE_OFF
};
enum SystemMode currentMode = MODE_STATIC;

CRGB leds[NUM_LEDS];
CRGB targetLeds[NUM_LEDS];

uint8_t SMOOTHING_SPEED = 40;

WebServer server(80);

// --- פונקציות עזר ---
void ledsSetup() {
  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.setCorrection(TypicalLEDStrip); // התיקון ללבן כחלחל
  FastLED.setBrightness(BRIGHTNESS);
  FastLED.clear();
  FastLED.show();
}

void runRainbow() {
  EVERY_N_MILLISECONDS(20) {
    hue++;
    fill_rainbow(leds, NUM_LEDS, hue, 7);
    FastLED.show();
  }
}

void runAmbilight() {
  if (Serial.available() < 6) return;
  if (Serial.read() != 'A') return; 
  if (Serial.read() != 'd') return; 
  if (Serial.read() != 'a') return; 

  unsigned char hibyte = Serial.read(); // Hi-Byte count
  unsigned char lobyte = Serial.read(); // Lo-Byte count
  unsigned char checksum = Serial.read(); // Checksum
  unsigned char result = hibyte ^ lobyte ^ 0x55; 
  if (result != checksum) return;

  Serial.readBytes((char*)targetLeds, NUM_LEDS * 3);
}

// --- Handlers ---

// דף הבית - קורא את הקובץ מהזיכרון ושולח לדפדפן
void handleRoot() {
  // פותח את הקובץ לקריאה (r)
  File file = LittleFS.open("/index.html", "r");
  
  if (!file) {
    server.send(500, "text/plain", "Error: index.html missing!");
    return;
  }
  
  // הזרמת הקובץ לדפדפן (יעיל מאוד)
  server.streamFile(file, "text/html");
  
  // סגירת הקובץ
  file.close();
}

// ה-API לשינוי צבע (נשאר אותו דבר)
void handleSetColor() {
  if (!server.hasArg("r") || !server.hasArg("g") || !server.hasArg("b")) {
    server.send(400, "text/plain", "Missing args");
    return;
  }

  int r = server.arg("r").toInt();
  int g = server.arg("g").toInt();
  int b = server.arg("b").toInt();

  currentMode = MODE_STATIC;

  fill_solid(leds, NUM_LEDS, CRGB(r, g, b));
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
  ledsSetup();

  // 1. אתחול מערכת הקבצים (Mounting)
  if (!LittleFS.begin()) {
    Serial.println("LittleFS Mount Failed. Formatting...");
    // אם נכשל, נפרמט וננסה שוב (קורה בפעם הראשונה)
    LittleFS.format();
    LittleFS.begin();
  } else {
    Serial.println("LittleFS Mounted Successfully");
  }

  // WiFi Initiate
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\nWiFi Connected: " + WiFi.localIP().toString());

  if (MDNS.begin(hostName)) {
    Serial.println("mDNS started: http://" + String(hostName) + ".local");
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
    runAmbilight();

    for (int i = 0; i < NUM_LEDS; i++)
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
        runRainbow();
        break;
      case MODE_OFF:
        break;
    }
  delay(2);
  }

}
#include <Arduino.h>
#include "AppConfig.h"
#include "LedController.h"
#include "WebController.h"

LedController mainLeds;

WebController webCtrl(mainLeds);

void setup() {
  Serial.setRxBufferSize(1024);

  Serial.begin(115200);
  Serial.setTimeout(1);

  AppConfig& cfg = AppConfig::get();
  cfg.loadConfig();  

  if (cfg.baud_rate != 115200) {
    Serial.flush();
    Serial.updateBaudRate(cfg.baud_rate);
    delay(100);
  }

  Serial.println("\n--- Ambilight System Starting ---");

  mainLeds.begin();
  webCtrl.begin();
}

void loop() {
  mainLeds.update();
  webCtrl.handleClient();
}
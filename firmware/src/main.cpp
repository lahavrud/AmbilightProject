#include <Arduino.h>
#include "AppConfig.h"
#include "LedController.h"
#include "WebController.h"
#include "SerialManager.h"

LedController mainLeds;
WebController webCtrl(mainLeds);
SerialManager serialMgr(mainLeds);

void setup() {
  Serial.setRxBufferSize(2048);

  AppConfig& cfg = AppConfig::get();
  cfg.loadConfig();  

  mainLeds.begin();
  serialMgr.begin();
  webCtrl.begin();
}

void loop() {
  serialMgr.process();
  webCtrl.handleClient();
  mainLeds.update();
}
// Trigger CI build test
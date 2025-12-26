#include <Arduino.h>
#include "AppConfig.h"
#include "LedController.h"
#include "WebController.h"
#include "PacketParser.h"
#include "SerialManager.h"

LedController mainLeds;
WebController webCtrl(mainLeds);
PacketParser parser(mainLeds);
SerialManager serialMgr(parser);

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
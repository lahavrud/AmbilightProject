#include <Arduino.h>
#include "AppConfig.h"
#include "LedController.h"
#include "WebController.h"
#include "PacketParser.h"
#include "UdpManager.h"
#include "SerialManager.h"

LedController mainLeds;
WebController webCtrl(mainLeds);
PacketParser parser(mainLeds);
UdpManager udpMgr(parser);
SerialManager serialMgr(parser);

void setup() {
  AppConfig& cfg = AppConfig::get();
  cfg.loadConfig();  

  serialMgr.begin();
  mainLeds.begin();
  webCtrl.begin();
  udpMgr.begin();
}

void loop() {
  webCtrl.handleClient();
  udpMgr.process();
  serialMgr.process();
  mainLeds.update();
}
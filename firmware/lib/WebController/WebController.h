#ifndef WEB_CONTROLLER_H
#define WEB_CONTROLLER_H

#include <WebServer.h>
#include "LedController.h"

class WebController {
private:
    WebServer server;
    LedController& leds;

    // --- Handlers ---
    void handleRoot();
    void handleGetConfig();
    void handleGetStatus();
    void handleSetColor();
    void handleSetBrightness();
    void handleSetMode();
    void handleNotFound();

public:
    WebController(LedController& ledCtrl);
    void begin(); 
    void handleClient(); 
};

#endif
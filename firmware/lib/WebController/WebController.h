#ifndef WEB_CONTROLLER_H
#define WEB_CONTROLLER_H

#include <WebServer.h>

class WebController {
private:
    WebServer server;

    // --- Handlers ---
    void handleRoot();
    void handleSetColor();
    void handleSetBrightness();
    void handleSetMode();
    void handleNotFound();

public:
    WebController();
    void begin(); 
    void handleClient(); 
};

#endif
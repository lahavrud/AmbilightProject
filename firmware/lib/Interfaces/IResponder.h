#ifndef I_RESPONDER_H
#define I_RESPONDER_H

#include <Arduino.h>

class IResponder {
public:
    virtual ~IResponder() {}
    virtual void sendResponse(const String& response) = 0;
};

#endif
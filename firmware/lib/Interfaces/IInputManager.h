#ifndef I_INPUT_MANAGER_H
#define I_INPUT_MANAGER_H

class IInputManager {
public:
    virtual ~IInputManager() {}

    virtual void begin() = 0;
    virtual void process() = 0;
};

#endif
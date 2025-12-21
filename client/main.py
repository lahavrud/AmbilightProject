import customtkinter as ctk
from src.models import AppMode
from src.app_controller import AmbilightApp, AppMode # הוספנו את AppMode ליתר ביטחון
from src.ui.main_window import MainWindow

if __name__ == "__main__":
    # 1. Initialize the Core Application Logic
    print("[Main] Initializing Core App...")
    app_logic = AmbilightApp()

    # 2. Start Background Threads
    # These will now respect the 'AppMode.OFF' state and wait patiently.
    app_logic.start_worker_thread()
    app_logic.start_tray_thread()

    # 3. Initialize the Main GUI Window
    print("[Main] Launching GUI...")
    window = MainWindow(app_logic)

    # 4. Define Cleanup Protocol
    def on_app_close():
        print("[Main] Shutdown initiated by user...")
        app_logic.stop_all()  
        window.destroy()      
        print("[Main] Goodbye.")

    window.protocol("WM_DELETE_WINDOW", on_app_close)

    # 5. Start the Main Event Loop
    # The GUI will now automatically sync with the controller's initial state
    window.mainloop()

# Trigger CI build test
import customtkinter as ctk
from src.app_controller import AmbilightApp
from src.ui.main_window import MainWindow

if __name__ == "__main__":
    # 1. Initialize the Core Application Logic
    # This loads configs, connects to serial, and prepares the engines.
    print("[Main] Initializing Core App...")
    app_logic = AmbilightApp()

    # 2. Start Background Threads
    # We start these BEFORE the GUI loop so they run immediately.
    
    # Start the screen capture & LED processing thread
    app_logic.start_worker_thread()
    
    # Start the System Tray icon thread
    app_logic.start_tray_thread()

    # 3. Initialize the Main GUI Window
    # We pass the 'app_logic' controller so the GUI can send commands.
    print("[Main] Launching GUI...")
    window = MainWindow(app_logic)

    # 4. Define Cleanup Protocol
    # This function runs when the user clicks 'X' on the window.
    def on_app_close():
        print("[Main] Shutdown initiated by user...")
        app_logic.stop_all()  # Stops LED thread and System Tray
        window.destroy()      # Closes the GUI window
        print("[Main] Goodbye.")

    # Bind the close event to our cleanup function
    window.protocol("WM_DELETE_WINDOW", on_app_close)

    # 5. Start the Main Event Loop (Blocking)
    # The code effectively pauses here until the window is closed.
    window.mainloop()
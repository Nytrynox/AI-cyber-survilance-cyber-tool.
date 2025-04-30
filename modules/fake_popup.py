import tkinter as tk
from tkinter import messagebox, PhotoImage
import os
import time
import random
import logging
import csv
from datetime import datetime
import threading

class FakePopupGenerator:
    """
    Generates convincing fake system popups for security testing and user behavior analysis.
    Used for educational purposes to demonstrate social engineering techniques.
    """
    
    def __init__(self, log_directory="../logs/"):
        """Initialize the FakePopupGenerator with logging capabilities."""
        self.log_directory = log_directory
        self.popup_log_file = os.path.join(log_directory, "popup_interactions.csv")
        self.running = False
        self.popup_thread = None
        self.popup_windows = []
        
        # Create log directory if it doesn't exist
        os.makedirs(log_directory, exist_ok=True)
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_directory, "popup_activity.log")),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("FakePopup")
        
        # Create popup log CSV if it doesn't exist
        if not os.path.exists(self.popup_log_file):
            with open(self.popup_log_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["timestamp", "popup_type", "message", "user_response"])
        
        self.logger.info("FakePopupGenerator initialized")
    
    def log_interaction(self, popup_type, message, user_response):
        """Log user interactions with popups to CSV file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.popup_log_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, popup_type, message, user_response])
        self.logger.info(f"User responded '{user_response}' to {popup_type} popup: '{message}'")
    
    def create_update_popup(self):
        """Create a fake system update popup."""
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Create a custom dialog that looks like a system popup
        popup = tk.Toplevel(root)
        popup.title("System Update Required")
        popup.geometry("400x250")
        popup.resizable(False, False)
        
        # Try to set window to always be on top
        popup.attributes('-topmost', True)
        
        # System icon (you would replace this with an actual path to an icon)
        try:
            # Using a system-like icon if available
            icon_path = os.path.join(os.path.dirname(__file__), "../assets/system_icon.png")
            if os.path.exists(icon_path):
                icon = PhotoImage(file=icon_path)
                popup.iconphoto(False, icon)
        except Exception as e:
            self.logger.warning(f"Could not load icon: {e}")
        
        # Header frame
        header_frame = tk.Frame(popup, bg="#0078D7", height=50)
        header_frame.pack(fill=tk.X)
        
        header_label = tk.Label(
            header_frame, 
            text="Important Security Update", 
            fg="white", 
            bg="#0078D7", 
            font=("Arial", 12, "bold")
        )
        header_label.pack(pady=10)
        
        # Content frame
        content_frame = tk.Frame(popup, bg="white")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        message_label = tk.Label(
            content_frame,
            text="Your system requires an important security update.\nWould you like to install this update now?",
            bg="white",
            font=("Arial", 10),
            justify=tk.LEFT,
            wraplength=350
        )
        message_label.pack(pady=20, padx=20, anchor="w")
        
        warning_label = tk.Label(
            content_frame,
            text="Postponing this update may leave your system vulnerable to security threats.",
            bg="white",
            fg="#CC0000",
            font=("Arial", 9),
            justify=tk.LEFT,
            wraplength=350
        )
        warning_label.pack(pady=5, padx=20, anchor="w")
        
        # Buttons frame
        button_frame = tk.Frame(content_frame, bg="white")
        button_frame.pack(pady=15, side=tk.BOTTOM, fill=tk.X)
        
        def install_clicked():
            self.log_interaction("system_update", "Security update required", "Install")
            popup.destroy()
            root.destroy()
        
        def later_clicked():
            self.log_interaction("system_update", "Security update required", "Later")
            popup.destroy()
            root.destroy()
        
        install_button = tk.Button(
            button_frame,
            text="Install Now",
            width=12,
            bg="#0078D7",
            fg="white",
            font=("Arial", 10),
            command=install_clicked
        )
        install_button.pack(side=tk.RIGHT, padx=10)
        
        later_button = tk.Button(
            button_frame,
            text="Later",
            width=10,
            font=("Arial", 10),
            command=later_clicked
        )
        later_button.pack(side=tk.RIGHT, padx=5)
        
        # Center the window on the screen
        popup.update_idletasks()
        width = popup.winfo_width()
        height = popup.winfo_height()
        x = (popup.winfo_screenwidth() // 2) - (width // 2)
        y = (popup.winfo_screenheight() // 2) - (height // 2)
        popup.geometry(f'{width}x{height}+{x}+{y}')
        
        self.popup_windows.append((root, popup))
        self.logger.info("Created system update popup")
        
        # Start the main loop for this window
        root.mainloop()
    
    def create_security_alert_popup(self):
        """Create a fake security alert popup."""
        root = tk.Tk()
        root.withdraw()
        
        response = messagebox.askquestion(
            "Security Alert",
            "Potential security threat detected! Your system may be at risk.\n\n"
            "Would you like to run a security scan now?",
            icon='warning'
        )
        
        self.log_interaction("security_alert", "Potential security threat detected", response)
        self.logger.info(f"Created security alert popup, response: {response}")
        
        root.destroy()
    
    def create_credential_verification_popup(self):
        """Create a fake credential verification popup."""
        root = tk.Tk()
        root.withdraw()
        
        popup = tk.Toplevel(root)
        popup.title("Account Verification Required")
        popup.geometry("400x300")
        popup.resizable(False, False)
        popup.attributes('-topmost', True)
        
        header_frame = tk.Frame(popup, bg="#333333", height=50)
        header_frame.pack(fill=tk.X)
        
        header_label = tk.Label(
            header_frame, 
            text="Account Verification", 
            fg="white", 
            bg="#333333", 
            font=("Arial", 12, "bold")
        )
        header_label.pack(pady=10)
        
        content_frame = tk.Frame(popup, bg="white")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        message_label = tk.Label(
            content_frame,
            text="Please verify your account credentials to continue.\nThis is required for security purposes.",
            bg="white",
            font=("Arial", 10),
            justify=tk.LEFT,
            wraplength=350
        )
        message_label.pack(pady=15, padx=20, anchor="w")
        
        # Username field
        username_frame = tk.Frame(content_frame, bg="white")
        username_frame.pack(fill=tk.X, padx=20, pady=5)
        
        username_label = tk.Label(
            username_frame,
            text="Username:",
            width=10,
            anchor="w",
            bg="white",
            font=("Arial", 10)
        )
        username_label.pack(side=tk.LEFT, padx=5)
        
        username_entry = tk.Entry(username_frame, width=30)
        username_entry.pack(side=tk.LEFT, padx=5)
        username_entry.insert(0, os.getlogin())  # Pre-fill with system username
        
        # Password field
        password_frame = tk.Frame(content_frame, bg="white")
        password_frame.pack(fill=tk.X, padx=20, pady=5)
        
        password_label = tk.Label(
            password_frame,
            text="Password:",
            width=10,
            anchor="w",
            bg="white",
            font=("Arial", 10)
        )
        password_label.pack(side=tk.LEFT, padx=5)
        
        password_entry = tk.Entry(password_frame, width=30, show="●")
        password_entry.pack(side=tk.LEFT, padx=5)
        
        # Button frame
        button_frame = tk.Frame(content_frame, bg="white")
        button_frame.pack(pady=20, side=tk.BOTTOM, fill=tk.X)
        
        def verify_clicked():
            username = username_entry.get()
            password = password_entry.get()
            if username and password:
                self.log_interaction(
                    "credential_verification", 
                    f"Username: {username}", 
                    "Credentials entered"
                )
                # We don't log the actual password for security/ethical reasons
                # This is a simulation tool for educational purposes only
            else:
                self.log_interaction(
                    "credential_verification", 
                    "Empty credentials", 
                    "Verification attempted"
                )
            popup.destroy()
            root.destroy()
        
        def cancel_clicked():
            self.log_interaction("credential_verification", "Verification prompt", "Canceled")
            popup.destroy()
            root.destroy()
        
        verify_button = tk.Button(
            button_frame,
            text="Verify",
            width=12,
            bg="#007ACC",
            fg="white",
            font=("Arial", 10),
            command=verify_clicked
        )
        verify_button.pack(side=tk.RIGHT, padx=10)
        
        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            width=10,
            font=("Arial", 10),
            command=cancel_clicked
        )
        cancel_button.pack(side=tk.RIGHT, padx=5)
        
        # Center the window
        popup.update_idletasks()
        width = popup.winfo_width()
        height = popup.winfo_height()
        x = (popup.winfo_screenwidth() // 2) - (width // 2)
        y = (popup.winfo_screenheight() // 2) - (height // 2)
        popup.geometry(f'{width}x{height}+{x}+{y}')
        
        self.popup_windows.append((root, popup))
        self.logger.info("Created credential verification popup")
        
        root.mainloop()
    
    def create_license_expired_popup(self):
        """Create a fake license expiration popup."""
        root = tk.Tk()
        root.withdraw()
        
        response = messagebox.showwarning(
            "License Expired",
            "Your software license has expired!\n\n"
            "Please renew your license to continue using all features.",
            type=messagebox.OK
        )
        
        self.log_interaction("license_expired", "Software license expired", "OK")
        self.logger.info("Created license expired popup")
        
        root.destroy()
    
    def random_popup(self):
        """Display a random fake popup."""
        popup_types = [
            self.create_update_popup,
            self.create_security_alert_popup,
            self.create_credential_verification_popup,
            self.create_license_expired_popup
        ]
        
        random.choice(popup_types)()
    
    def start_random_popups(self, min_interval=1800, max_interval=3600):
        """
        Start displaying random popups at random intervals.
        
        Args:
            min_interval: Minimum seconds between popups (default: 30 minutes)
            max_interval: Maximum seconds between popups (default: 60 minutes)
        """
        self.running = True
        
        def popup_loop():
            while self.running:
                # Random delay between popups
                delay = random.randint(min_interval, max_interval)
                self.logger.info(f"Next popup scheduled in {delay} seconds")
                time.sleep(delay)
                
                if not self.running:
                    break
                
                # Display a random popup
                self.random_popup()
        
        self.popup_thread = threading.Thread(target=popup_loop)
        self.popup_thread.daemon = True
        self.popup_thread.start()
        self.logger.info(f"Started random popup generator (interval: {min_interval}-{max_interval}s)")
    
    def stop_popups(self):
        """Stop the random popup generator."""
        self.running = False
        if self.popup_thread:
            self.popup_thread.join(1.0)
        
        # Close any open popups
        for root, popup in self.popup_windows:
            try:
                popup.destroy()
                root.destroy()
            except:
                pass
        
        self.popup_windows = []
        self.logger.info("Stopped popup generator")
    
    def create_custom_popup(self, title, message, popup_type="info"):
        """
        Create a custom popup with specified parameters.
        
        Args:
            title: The title of the popup
            message: The message to display
            popup_type: Type of popup (info, warning, error)
        """
        root = tk.Tk()
        root.withdraw()
        
        if popup_type == "info":
            response = messagebox.showinfo(title, message)
        elif popup_type == "warning":
            response = messagebox.showwarning(title, message)
        elif popup_type == "error":
            response = messagebox.showerror(title, message)
        else:
            response = messagebox.askquestion(title, message)
        
        self.log_interaction("custom_popup", f"{title}: {message}", str(response))
        self.logger.info(f"Created custom {popup_type} popup: {title}")
        
        root.destroy()


# Example usage when run directly
if __name__ == "__main__":
    popup_gen = FakePopupGenerator()
    
    # Test each popup type
    print("Testing update popup...")
    popup_gen.create_update_popup()
    
    print("Testing security alert popup...")
    popup_gen.create_security_alert_popup()
    
    print("Testing credential verification popup...")
    popup_gen.create_credential_verification_popup()
    
    print("Testing license expired popup...")
    popup_gen.create_license_expired_popup()
    
    # Test random popups for 60 seconds with short intervals
    print("Testing random popups (will run for 60 seconds)...")
    popup_gen.start_random_popups(min_interval=10, max_interval=20)
    time.sleep(60)
    popup_gen.stop_popups()
    
    print("All tests complete!")
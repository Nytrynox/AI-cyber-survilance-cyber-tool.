#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ReconEngine: Core reconnaissance module for SpecterX
Handles webcam-based surveillance, emotion detection, and system information gathering
"""

import os
import csv
import time
import platform
import socket
import uuid
import psutil
import cv2
import numpy as np
from datetime import datetime
import pandas as pd
import logging
from pathlib import Path
import threading
import warnings

# For emotion detection
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    warnings.warn("DeepFace not available, emotion detection will be disabled")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/specter_recon.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("ReconEngine")

class ReconEngine:
    """
    Primary reconnaissance engine for SpecterX.
    Handles webcam surveillance, emotion detection, and system information gathering.
    """
    
    def __init__(self, config=None):
        """
        Initialize the ReconEngine with configuration settings
        
        Args:
            config (dict): Configuration parameters
        """
        self.config = {
            'camera_index': 0,
            'frame_interval': 0.1,  # seconds between frame captures
            'emotion_detection': DEEPFACE_AVAILABLE,
            'emotion_interval': 3,  # seconds between emotion analyses
            'recon_log_path': 'logs/recon_logs.csv',
            'screenshot_dir': 'logs/screenshots/',
            'webcam_dir': 'logs/webcam/',
            'recording': False,
            'resolution': (640, 480),
        }
        
        if config:
            self.config.update(config)
        
        # Create necessary directories
        for directory in [self.config['screenshot_dir'], self.config['webcam_dir']]:
            os.makedirs(directory, exist_ok=True)
            
        # Initialize resources to None
        self.cap = None
        self.recording_thread = None
        self.stop_event = threading.Event()
        self.last_emotion_time = 0
        
        # Check log file exists, create with headers if not
        self._initialize_log_file()
        
        logger.info("ReconEngine initialized successfully")
    
    def _initialize_log_file(self):
        """Create recon log file with headers if it doesn't exist"""
        log_path = self.config['recon_log_path']
        
        if not os.path.exists(log_path):
            Path(log_path).parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'username', 'os', 'hostname', 'ip_address', 
                    'mac_address', 'cpu_usage', 'memory_usage', 'active_window',
                    'emotion', 'emotion_confidence', 'webcam_file', 'screenshot_file'
                ])
    
    def start(self):
        """Start the reconnaissance engine and begin monitoring"""
        try:
            # Initialize camera
            self.cap = cv2.VideoCapture(self.config['camera_index'])
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config['resolution'][0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config['resolution'][1])
            
            if not self.cap.isOpened():
                logger.error("Failed to open webcam")
                return False
            
            # Reset stop event
            self.stop_event.clear()
            
            # Start recording in separate thread if enabled
            if self.config['recording']:
                self.recording_thread = threading.Thread(target=self._recording_loop)
                self.recording_thread.daemon = True
                self.recording_thread.start()
                logger.info("Reconnaissance recording started")
            
            return True
        
        except Exception as e:
            logger.error(f"Error starting ReconEngine: {str(e)}")
            return False
    
    def stop(self):
        """Stop the reconnaissance engine and release resources"""
        try:
            # Signal recording thread to stop
            self.stop_event.set()
            
            # Wait for recording thread to finish
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=5)
            
            # Release camera
            if self.cap:
                self.cap.release()
                self.cap = None
            
            logger.info("ReconEngine stopped")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping ReconEngine: {str(e)}")
            return False
    
    def _recording_loop(self):
        """Main recording loop that captures frames and system information"""
        while not self.stop_event.is_set():
            try:
                # Capture a frame from webcam
                ret, frame = self.cap.read()
                
                if not ret:
                    logger.warning("Failed to capture frame")
                    time.sleep(self.config['frame_interval'])
                    continue
                
                # Generate filenames
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                webcam_file = f"{self.config['webcam_dir']}{timestamp}.jpg"
                screenshot_file = f"{self.config['screenshot_dir']}{timestamp}.png"
                
                # Save webcam frame
                cv2.imwrite(webcam_file, frame)
                
                # Detect emotion if enabled and interval passed
                emotion_data = {'emotion': 'unknown', 'confidence': 0.0}
                current_time = time.time()
                if (self.config['emotion_detection'] and 
                    current_time - self.last_emotion_time >= self.config['emotion_interval']):
                    emotion_data = self._detect_emotion(frame)
                    self.last_emotion_time = current_time
                
                # Get system information
                system_info = self._gather_system_info()
                
                # Log reconnaissance data
                self._log_recon_data(
                    system_info=system_info,
                    emotion_data=emotion_data,
                    webcam_file=os.path.basename(webcam_file),
                    screenshot_file=os.path.basename(screenshot_file)
                )
                
                # Sleep before next capture
                time.sleep(self.config['frame_interval'])
                
            except Exception as e:
                logger.error(f"Error in recording loop: {str(e)}")
                time.sleep(1)  # Sleep longer on error
    
    def _detect_emotion(self, frame):
        """
        Detect emotion in a given frame using DeepFace
        
        Args:
            frame (numpy.ndarray): CV2 image frame
            
        Returns:
            dict: Emotion data containing emotion type and confidence
        """
        if not DEEPFACE_AVAILABLE:
            return {'emotion': 'unknown', 'confidence': 0.0}
        
        try:
            # Convert BGR to RGB for DeepFace
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Analyze emotion
            result = DeepFace.analyze(
                img_path=rgb_frame,
                actions=['emotion'],
                enforce_detection=False,
                detector_backend='opencv'
            )
            
            if isinstance(result, list):
                result = result[0]  # Get first face if multiple detected
                
            dominant_emotion = result['dominant_emotion']
            emotion_scores = result['emotion']
            confidence = emotion_scores[dominant_emotion]
            
            return {'emotion': dominant_emotion, 'confidence': confidence}
            
        except Exception as e:
            logger.warning(f"Emotion detection failed: {str(e)}")
            return {'emotion': 'unknown', 'confidence': 0.0}
    
    def _gather_system_info(self):
        """
        Gather current system information
        
        Returns:
            dict: System information data
        """
        try:
            # Get basic system info
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                                  for elements in range(0, 48, 8)][::-1])
            
            # Get performance metrics
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            
            # Get active window (placeholder - platform specific code needed)
            active_window = self._get_active_window()
            
            return {
                'username': os.getlogin(),
                'os': f"{platform.system()} {platform.release()}",
                'hostname': hostname,
                'ip_address': ip_address,
                'mac_address': mac_address,
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'active_window': active_window
            }
            
        except Exception as e:
            logger.error(f"Error gathering system info: {str(e)}")
            return {
                'username': 'unknown',
                'os': 'unknown',
                'hostname': 'unknown',
                'ip_address': 'unknown',
                'mac_address': 'unknown',
                'cpu_usage': 0,
                'memory_usage': 0,
                'active_window': 'unknown'
            }
    
    def _get_active_window(self):
        """
        Get the title of the currently active window (platform-specific implementation)
        
        Returns:
            str: Active window title or 'unknown'
        """
        try:
            current_platform = platform.system().lower()
            
            if current_platform == 'windows':
                # Windows implementation
                try:
                    import win32gui
                    window = win32gui.GetForegroundWindow()
                    return win32gui.GetWindowText(window)
                except ImportError:
                    return "win32gui not available"
                
            elif current_platform == 'darwin':  # macOS
                try:
                    # Using AppleScript through osascript
                    import subprocess
                    cmd = """osascript -e 'tell application "System Events"
                             set frontApp to name of first application process whose frontmost is true
                             end tell'"""
                    output = subprocess.check_output(cmd, shell=True).decode().strip()
                    return output
                except Exception:
                    return "osascript error"
                
            elif current_platform == 'linux':
                try:
                    # Using xdotool if available
                    import subprocess
                    cmd = "xdotool getwindowfocus getwindowname"
                    output = subprocess.check_output(cmd, shell=True).decode().strip()
                    return output
                except Exception:
                    return "xdotool error"
            
            return f"Unsupported platform: {current_platform}"
            
        except Exception as e:
            logger.warning(f"Could not determine active window: {str(e)}")
            return "unknown"
    
    def _log_recon_data(self, system_info, emotion_data, webcam_file, screenshot_file):
        """
        Log reconnaissance data to CSV file
        
        Args:
            system_info (dict): System information data
            emotion_data (dict): Emotion detection results
            webcam_file (str): Path to saved webcam image
            screenshot_file (str): Path to saved screenshot
        """
        try:
            timestamp = datetime.now().isoformat()
            
            with open(self.config['recon_log_path'], 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp,
                    system_info['username'],
                    system_info['os'],
                    system_info['hostname'],
                    system_info['ip_address'],
                    system_info['mac_address'],
                    system_info['cpu_usage'],
                    system_info['memory_usage'],
                    system_info['active_window'],
                    emotion_data['emotion'],
                    emotion_data['confidence'],
                    webcam_file,
                    screenshot_file
                ])
                
        except Exception as e:
            logger.error(f"Error logging recon data: {str(e)}")
    
    def take_snapshot(self):
        """
        Take an immediate snapshot with webcam and system info
        
        Returns:
            dict: Snapshot data including system info, webcam image path, and emotion data
        """
        if not self.cap or not self.cap.isOpened():
            if not self.start():
                logger.error("Failed to start camera for snapshot")
                return None
        
        try:
            # Capture frame
            ret, frame = self.cap.read()
            if not ret:
                logger.error("Failed to capture snapshot frame")
                return None
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            webcam_file = f"{self.config['webcam_dir']}{timestamp}.jpg"
            
            # Save webcam frame
            cv2.imwrite(webcam_file, frame)
            
            # Detect emotion
            emotion_data = self._detect_emotion(frame) if self.config['emotion_detection'] else {'emotion': 'unknown', 'confidence': 0.0}
            
            # Get system information
            system_info = self._gather_system_info()
            
            # Log the snapshot
            self._log_recon_data(
                system_info=system_info,
                emotion_data=emotion_data,
                webcam_file=os.path.basename(webcam_file),
                screenshot_file="none"
            )
            
            return {
                'system_info': system_info,
                'emotion': emotion_data,
                'webcam_file': webcam_file,
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Error taking snapshot: {str(e)}")
            return None
    
    def get_recent_logs(self, limit=10):
        """
        Get the most recent reconnaissance logs
        
        Args:
            limit (int): Maximum number of logs to return
            
        Returns:
            list: List of recent log entries as dictionaries
        """
        try:
            if not os.path.exists(self.config['recon_log_path']):
                return []
            
            df = pd.read_csv(self.config['recon_log_path'])
            df = df.sort_values('timestamp', ascending=False).head(limit)
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error retrieving recent logs: {str(e)}")
            return []
    
    def get_emotion_summary(self, timeframe='day'):
        """
        Get a summary of emotions detected over a specified timeframe
        
        Args:
            timeframe (str): 'hour', 'day', 'week', or 'all'
            
        Returns:
            dict: Summary of emotions and their frequencies
        """
        try:
            if not os.path.exists(self.config['recon_log_path']):
                return {'unknown': 100.0}
            
            df = pd.read_csv(self.config['recon_log_path'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filter by timeframe
            now = datetime.now()
            if timeframe == 'hour':
                df = df[df['timestamp'] > (now - pd.Timedelta(hours=1))]
            elif timeframe == 'day':
                df = df[df['timestamp'] > (now - pd.Timedelta(days=1))]
            elif timeframe == 'week':
                df = df[df['timestamp'] > (now - pd.Timedelta(weeks=1))]
            
            # Count emotions
            if df.empty:
                return {'unknown': 100.0}
            
            emotion_counts = df['emotion'].value_counts(normalize=True) * 100
            return emotion_counts.to_dict()
            
        except Exception as e:
            logger.error(f"Error generating emotion summary: {str(e)}")
            return {'unknown': 100.0}


if __name__ == "__main__":
    # Example usage
    engine = ReconEngine()
    print("Starting ReconEngine...")
    engine.start()
    
    try:
        print("Taking initial snapshot...")
        snapshot = engine.take_snapshot()
        print(f"Snapshot taken: {snapshot['timestamp']}")
        print(f"Detected emotion: {snapshot['emotion']['emotion']} ({snapshot['emotion']['confidence']:.2f})")
        
        print("ReconEngine running... Press Ctrl+C to stop")
        # Run for a while to collect data
        time.sleep(60)
        
    except KeyboardInterrupt:
        print("\nStopping ReconEngine...")
    finally:
        engine.stop()
        
        # Show a summary of collected data
        recent_logs = engine.get_recent_logs(5)
        print(f"\nRecent activity ({len(recent_logs)} entries):")
        for log in recent_logs:
            print(f"- {log['timestamp']}: {log['emotion']} ({log['active_window']})")
        
        emotion_summary = engine.get_emotion_summary('all')
        print("\nEmotion summary:")
        for emotion, percentage in emotion_summary.items():
            print(f"- {emotion}: {percentage:.1f}%")
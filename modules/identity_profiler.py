"""
SpecterX Identity Profiler Module
---------------------------------
This module handles facial recognition, emotion detection, and user behavior profiling
through webcam analysis. It captures images, processes them with AI models, and stores
user identity and emotional data for security analysis.
"""

import cv2
import numpy as np
import pandas as pd
import datetime
import time
import os
import threading
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Union, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/identity_profiler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("identity_profiler")

class IdentityProfiler:
    """
    Class responsible for webcam-based user identification and emotion detection.
    Uses computer vision and AI models to analyze facial expressions and behaviors.
    """
    
    def __init__(self, 
                 profile_dir: str = "profiles", 
                 camera_index: int = 0, 
                 emotion_detection: bool = True,
                 capture_interval: int = 30):
        """
        Initialize the Identity Profiler module.
        
        Args:
            profile_dir: Directory to store user profile data
            camera_index: Index of the webcam to use
            emotion_detection: Whether to enable emotion detection
            capture_interval: Seconds between captures in monitoring mode
        """
        self.profile_dir = Path(profile_dir)
        self.profile_dir.mkdir(exist_ok=True)
        
        self.camera_index = camera_index
        self.emotion_detection = emotion_detection
        self.capture_interval = capture_interval
        
        # Load AI models
        self._load_models()
        
        # Create storage for current session data
        self.current_profile = {
            "user_id": None,
            "timestamp": [],
            "emotion": [],
            "confidence": [],
            "face_detected": []
        }
        
        # Status tracking
        self.is_running = False
        self.monitor_thread = None
        self.cap = None

    def _load_models(self):
        """Load the required AI models for face detection and emotion analysis."""
        try:
            # Load face detection model
            model_path = Path(__file__).parent.parent / "models"
            face_cascade_path = str(model_path / "haarcascade_frontalface_default.xml")
            
            # Create models directory if it doesn't exist
            model_path.mkdir(exist_ok=True)
            
            # If model doesn't exist, use OpenCV's built-in one
            if not os.path.exists(face_cascade_path):
                face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            
            self.face_cascade = cv2.CascadeClassifier(face_cascade_path)
            
            # Load emotion detection model (simulated for demonstration)
            # In a real implementation, this would load a proper deep learning model
            self.emotion_model = self._create_dummy_emotion_model()
            
            logger.info("AI models loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load AI models: {str(e)}")
            raise RuntimeError("Failed to initialize required AI models")

    def _create_dummy_emotion_model(self):
        """
        Create a simple dummy emotion detection model for demonstration.
        In a real implementation, this would be replaced with a proper CNN or other deep learning model.
        """
        class DummyEmotionModel:
            def predict(self, face_img):
                # Simulate emotion detection with random values
                emotions = ["neutral", "happy", "sad", "angry", "surprised", "fearful", "disgusted"]
                probabilities = np.random.random(len(emotions))
                probabilities = probabilities / np.sum(probabilities)  # Normalize
                
                # Return the emotion with highest probability
                emotion = emotions[np.argmax(probabilities)]
                confidence = float(np.max(probabilities))
                
                return emotion, confidence
                
        return DummyEmotionModel()

    def start_camera(self) -> bool:
        """
        Initialize and start the webcam.
        
        Returns:
            bool: Whether camera was successfully started
        """
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera at index {self.camera_index}")
                return False
                
            logger.info(f"Camera started successfully at index {self.camera_index}")
            return True
        except Exception as e:
            logger.error(f"Error starting camera: {str(e)}")
            return False

    def stop_camera(self) -> None:
        """Release the webcam."""
        if self.cap and self.cap.isOpened():
            self.cap.release()
            logger.info("Camera released")

    def capture_frame(self) -> Tuple[bool, np.ndarray]:
        """
        Capture a single frame from the webcam.
        
        Returns:
            Tuple[bool, np.ndarray]: Success flag and the captured frame
        """
        if not self.cap or not self.cap.isOpened():
            if not self.start_camera():
                return False, None
                
        ret, frame = self.cap.read()
        if not ret:
            logger.error("Failed to capture frame")
            return False, None
            
        return True, frame

    def detect_face(self, frame: np.ndarray) -> Tuple[bool, Optional[np.ndarray], Optional[Tuple[int, int, int, int]]]:
        """
        Detect a face in the given frame.
        
        Args:
            frame: Input image frame
            
        Returns:
            Tuple containing:
                - Whether a face was detected
                - Face image if detected, None otherwise
                - Face coordinates (x, y, w, h) if detected, None otherwise
        """
        if frame is None:
            return False, None, None
            
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        # Process the largest face if any were detected
        if len(faces) > 0:
            # Find the largest face
            largest_face_idx = np.argmax([w*h for (x, y, w, h) in faces])
            x, y, w, h = faces[largest_face_idx]
            
            # Extract face region
            face_img = frame[y:y+h, x:x+w]
            
            return True, face_img, (x, y, w, h)
        else:
            return False, None, None

    def analyze_emotion(self, face_img: np.ndarray) -> Tuple[str, float]:
        """
        Analyze the emotion of a detected face.
        
        Args:
            face_img: Image of the detected face
            
        Returns:
            Tuple of emotion label and confidence score
        """
        if face_img is None or not self.emotion_detection:
            return "unknown", 0.0
            
        try:
            # Preprocess face image for emotion model
            # Resize to expected input size
            face_img_resized = cv2.resize(face_img, (48, 48))
            face_img_gray = cv2.cvtColor(face_img_resized, cv2.COLOR_BGR2GRAY)
            
            # Get emotion prediction
            emotion, confidence = self.emotion_model.predict(face_img_gray)
            
            return emotion, confidence
        except Exception as e:
            logger.error(f"Error analyzing emotion: {str(e)}")
            return "error", 0.0

    def save_profile_image(self, face_img: np.ndarray, user_id: str = None) -> str:
        """
        Save a captured face image to the profile directory.
        
        Args:
            face_img: Face image to save
            user_id: Optional user ID, will be generated if not provided
            
        Returns:
            String user ID
        """
        if user_id is None:
            # Generate a new user ID based on timestamp
            user_id = f"user_{int(time.time())}"
            
        # Create user directory if it doesn't exist
        user_dir = self.profile_dir / user_id
        user_dir.mkdir(exist_ok=True)
        
        # Save the image
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = user_dir / f"{timestamp}.jpg"
        
        cv2.imwrite(str(image_path), face_img)
        logger.info(f"Saved profile image to {image_path}")
        
        return user_id

    def process_frame(self, frame: np.ndarray) -> Dict:
        """
        Process a single frame to detect face and analyze emotion.
        
        Args:
            frame: Input image frame
            
        Returns:
            Dict with processed results
        """
        result = {
            "timestamp": datetime.datetime.now(),
            "face_detected": False,
            "emotion": "unknown",
            "confidence": 0.0,
            "face_location": None,
            "user_id": self.current_profile["user_id"]
        }
        
        # Detect face
        face_detected, face_img, face_location = self.detect_face(frame)
        result["face_detected"] = face_detected
        result["face_location"] = face_location
        
        if face_detected:
            # Analyze emotion if face was detected
            emotion, confidence = self.analyze_emotion(face_img)
            result["emotion"] = emotion
            result["confidence"] = confidence
            
            # Save profile data
            if self.current_profile["user_id"] is None:
                user_id = self.save_profile_image(face_img)
                self.current_profile["user_id"] = user_id
                result["user_id"] = user_id
            else:
                # Periodically save new images
                if len(self.current_profile["timestamp"]) % 10 == 0:
                    self.save_profile_image(face_img, self.current_profile["user_id"])
            
            # Update profile data
            self.current_profile["timestamp"].append(result["timestamp"])
            self.current_profile["emotion"].append(emotion)
            self.current_profile["confidence"].append(confidence)
            self.current_profile["face_detected"].append(True)
            
        return result

    def start_monitoring(self) -> bool:
        """
        Start continuous monitoring in a separate thread.
        
        Returns:
            bool: Whether monitoring was successfully started
        """
        if self.is_running:
            logger.warning("Monitoring already running")
            return False
            
        if not self.start_camera():
            return False
            
        # Reset current profile
        self.current_profile = {
            "user_id": None,
            "timestamp": [],
            "emotion": [],
            "confidence": [],
            "face_detected": []
        }
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("Started continuous monitoring")
        return True

    def stop_monitoring(self) -> None:
        """Stop the continuous monitoring thread."""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
            logger.info("Stopped continuous monitoring")
        
        self.stop_camera()
        self._save_session_data()

    def _monitoring_loop(self) -> None:
        """Background thread that continuously monitors using the webcam."""
        try:
            while self.is_running:
                success, frame = self.capture_frame()
                
                if success:
                    result = self.process_frame(frame)
                    
                    # Optional: Display the processed frame with annotations
                    if result["face_detected"]:
                        x, y, w, h = result["face_location"]
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        
                        # Display emotion
                        emotion_text = f"{result['emotion']} ({result['confidence']:.2f})"
                        cv2.putText(frame, emotion_text, (x, y-10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Sleep for the specified interval
                time.sleep(self.capture_interval)
                
        except Exception as e:
            logger.error(f"Error in monitoring loop: {str(e)}")
            self.is_running = False
        finally:
            self.stop_camera()

    def _save_session_data(self) -> None:
        """Save the current session data to a CSV file."""
        if len(self.current_profile["timestamp"]) == 0:
            logger.info("No session data to save")
            return
            
        try:
            # Create a DataFrame from the profile data
            df = pd.DataFrame({
                "timestamp": self.current_profile["timestamp"],
                "emotion": self.current_profile["emotion"],
                "confidence": self.current_profile["confidence"],
                "face_detected": self.current_profile["face_detected"],
                "user_id": [self.current_profile["user_id"]] * len(self.current_profile["timestamp"])
            })
            
            # Save to CSV
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            user_id = self.current_profile["user_id"] or "unknown"
            
            # Ensure the logs directory exists
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            
            # Save the file
            csv_path = logs_dir / f"profile_{user_id}_{timestamp}.csv"
            df.to_csv(csv_path, index=False)
            
            logger.info(f"Saved session data to {csv_path}")
        except Exception as e:
            logger.error(f"Error saving session data: {str(e)}")

    def get_single_profile(self) -> Dict:
        """
        Capture a single profile snapshot.
        
        Returns:
            Dict with profile data
        """
        if not self.start_camera():
            return {"error": "Failed to start camera"}
            
        try:
            success, frame = self.capture_frame()
            if not success:
                return {"error": "Failed to capture frame"}
                
            result = self.process_frame(frame)
            self.stop_camera()
            
            return result
        except Exception as e:
            logger.error(f"Error getting single profile: {str(e)}")
            self.stop_camera()
            return {"error": str(e)}

    def get_emotion_history(self) -> pd.DataFrame:
        """
        Get the emotion history for the current session.
        
        Returns:
            DataFrame with emotion history
        """
        if len(self.current_profile["timestamp"]) == 0:
            return pd.DataFrame()
            
        df = pd.DataFrame({
            "timestamp": self.current_profile["timestamp"],
            "emotion": self.current_profile["emotion"],
            "confidence": self.current_profile["confidence"]
        })
        
        return df

    def get_dominant_emotion(self) -> Tuple[str, float]:
        """
        Calculate the dominant emotion for the current session.
        
        Returns:
            Tuple of dominant emotion and its frequency
        """
        if len(self.current_profile["emotion"]) == 0:
            return "unknown", 0.0
            
        # Count occurrences of each emotion
        emotion_counts = {}
        for emotion in self.current_profile["emotion"]:
            if emotion not in emotion_counts:
                emotion_counts[emotion] = 0
            emotion_counts[emotion] += 1
            
        # Find the most frequent emotion
        dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])
        
        # Calculate the frequency
        frequency = dominant_emotion[1] / len(self.current_profile["emotion"])
        
        return dominant_emotion[0], frequency

    def clear_current_profile(self) -> None:
        """Reset the current profile data."""
        self.current_profile = {
            "user_id": None,
            "timestamp": [],
            "emotion": [],
            "confidence": [],
            "face_detected": []
        }
        logger.info("Cleared current profile data")

    def draw_emotion_overlay(self, frame: np.ndarray, result: Dict) -> np.ndarray:
        """
        Draw emotion detection results as an overlay on the frame.
        
        Args:
            frame: Input image frame
            result: Result dictionary from process_frame
            
        Returns:
            Frame with overlay
        """
        if frame is None:
            return None
            
        frame_copy = frame.copy()
        
        if result["face_detected"]:
            x, y, w, h = result["face_location"]
            
            # Draw face rectangle
            cv2.rectangle(frame_copy, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Display emotion
            emotion_text = f"{result['emotion']} ({result['confidence']:.2f})"
            cv2.putText(frame_copy, emotion_text, (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Draw user ID if available
            if result["user_id"]:
                cv2.putText(frame_copy, f"ID: {result['user_id']}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        else:
            # No face detected message
            cv2.putText(frame_copy, "No face detected", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
        # Add timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame_copy, timestamp, (10, frame_copy.shape[0] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame_copy

    def get_user_profile_summary(self, user_id: str = None) -> Dict:
        """
        Generate a summary of the user's profile.
        
        Args:
            user_id: User ID to summarize, uses current user if None
            
        Returns:
            Dictionary with profile summary
        """
        if user_id is None:
            user_id = self.current_profile["user_id"]
            
        if user_id is None:
            return {"error": "No user ID specified"}
            
        # Try to load profile data
        user_dir = self.profile_dir / user_id
        if not user_dir.exists():
            return {"error": f"User profile not found: {user_id}"}
            
        # Count images
        image_count = len(list(user_dir.glob("*.jpg")))
        
        # Calculate summary from current session if it's the current user
        if user_id == self.current_profile["user_id"] and len(self.current_profile["emotion"]) > 0:
            dominant_emotion, frequency = self.get_dominant_emotion()
            
            return {
                "user_id": user_id,
                "image_count": image_count,
                "session_frames": len(self.current_profile["timestamp"]),
                "dominant_emotion": dominant_emotion,
                "emotion_frequency": frequency,
                "last_seen": max(self.current_profile["timestamp"]) if self.current_profile["timestamp"] else None
            }
        else:
            # Basic summary without session data
            return {
                "user_id": user_id,
                "image_count": image_count,
                "session_frames": 0,
                "last_seen": datetime.datetime.fromtimestamp(
                    max(os.path.getmtime(f) for f in user_dir.glob("*.jpg"))
                ) if image_count > 0 else None
            }


# Example usage
if __name__ == "__main__":
    # Create an instance of the profiler
    profiler = IdentityProfiler(capture_interval=5)
    
    # Start monitoring for 30 seconds
    if profiler.start_monitoring():
        print("Monitoring started. Press Ctrl+C to stop...")
        try:
            # Run for 30 seconds
            time.sleep(30)
        except KeyboardInterrupt:
            print("Monitoring interrupted.")
        finally:
            profiler.stop_monitoring()
            
    # Display the results
    if profiler.current_profile["user_id"]:
        dominant_emotion, frequency = profiler.get_dominant_emotion()
        print(f"User ID: {profiler.current_profile['user_id']}")
        print(f"Dominant Emotion: {dominant_emotion} ({frequency:.2f})")
        print(f"Frames Analyzed: {len(profiler.current_profile['timestamp'])}")
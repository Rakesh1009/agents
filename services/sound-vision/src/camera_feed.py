import cv2
import time

class CameraFeed:
    """Handles video ingestion from a source (typically /dev/video0)."""
    
    def __init__(self, source=0, target_fps=5):
        self.source = source
        self.target_fps = target_fps
        self.cap = cv2.VideoCapture(source)
        
        if not self.cap.isOpened():
            print(f"Error: Could not open video source {source}")
            
        # We don't need high resolution for YOLO to just see a person
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.last_frame_time = 0

    def get_frame(self):
        """Grabs a frame, pacing it to the target FPS."""
        if not self.cap.isOpened():
            return False, None
            
        current_time = time.time()
        elapsed = current_time - self.last_frame_time
        time_to_wait = (1.0 / self.target_fps) - elapsed
        
        # If we are grabbing too fast, sleep briefly
        if time_to_wait > 0:
            time.sleep(time_to_wait)
            
        ret, frame = self.cap.read()
        if ret:
            self.last_frame_time = time.time()
            
        return ret, frame

    def release(self):
        self.cap.release()

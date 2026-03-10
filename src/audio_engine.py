import pyttsx3
import threading
import queue
import time

class AudioEngine:
    """A non-blocking text-to-speech engine with message throttling and volume control."""
    
    def __init__(self, throttle_seconds=3.0, muted=False):
        self.message_queue = queue.Queue()
        self.throttle_seconds = throttle_seconds
        self.muted = muted
        
        # Keep track of what we last said and when, to avoid repeating constantly
        self.last_message = ""
        self.last_message_time = 0
        
        # Start the background worker thread
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()

    def _process_queue(self):
        """Background thread loop that pulls from queue and speaks."""
        # pyttsx3 needs to be initialized in the thread that acts on it
        try:
            engine = pyttsx3.init()
        except Exception as e:
            print(f"[AUDIO OUT ERROR] Could not initialize pyttsx3: {e}")
            engine = None
        
        while True:
            try:
                # Block until a message is available
                message = self.message_queue.get()
                
                # Check throttling
                current_time = time.time()
                time_since_last = current_time - self.last_message_time
                
                # Only speak if it's a new message, OR enough time has passed
                if message != self.last_message or time_since_last > self.throttle_seconds:
                    if self.muted:
                        print(f"[AUDIO OUT (MUTED)] -> {message}")
                    else:
                        print(f"[AUDIO OUT] -> {message}")
                        if engine:
                            engine.say(message)
                            engine.runAndWait()
                    
                    self.last_message = message
                    self.last_message_time = time.time()
                else:
                    # Message throttled (skipped)
                    pass
                    
            except Exception as e:
                print(f"Audio Engine Error: {e}")
            finally:
                self.message_queue.task_done()

    def queue_message(self, text, priority="normal"):
        """Adds a message to the speech queue."""
        if self.message_queue.qsize() < 2:
            self.message_queue.put(text)

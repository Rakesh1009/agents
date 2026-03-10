import time
import cv2
import argparse
from camera_feed import CameraFeed
from detector import ObjectDetector
from context_engine import ContextEngine
from audio_engine import AudioEngine

def main():
    parser = argparse.ArgumentParser(description="Sound-Vision Assistive Workflow")
    parser.add_argument("--mute", action="store_true", help="Disable audio output (for office testing)")
    args = parser.parse_args()

    print("Initializing Sound-Vision Assistive Workflow...")
    print(f"Audio Output: {'MUTED' if args.mute else 'ENABLED'}")
    
    try:
        camera = CameraFeed(source=0, target_fps=5)
        detector = ObjectDetector(model_name="yolov8n.pt", target_classes=[0]) # 0 = Person
        context_engine = ContextEngine()
        audio = AudioEngine(throttle_seconds=3.0, muted=args.mute)
    except Exception as e:
        print(f"Failed to initialize components: {e}")
        return

    print("Pipeline ready. Starting processing loop... Press 'q' in the video window to quit.")
    audio.queue_message("System Online.")
    
    try:
        while True:
            # 1. Ingestion
            ret, frame = camera.get_frame()
            if not ret or frame is None:
                time.sleep(0.01)
                continue
                
            # Update context engine with current frame dimensions
            context_engine.frame_height, context_engine.frame_width = frame.shape[:2]
            
            # 2. Detection
            detections = detector.detect(frame)
            
            # Prepare overlay text
            display_text = "No person detected"
            
            # 3. Context & Translation
            if detections:
                context = context_engine.process_detections(detections)
                
                # Draw boxes for debugging
                for det in detections:
                    x1, y1, x2, y2 = map(int, det["bbox"])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                if context and context.get("text"):
                    display_text = context["text"]
                    
                    # 4. Audio Plugin
                    audio.queue_message(context["text"], priority=context.get("priority", "normal"))
            
            # --- VISUAL DEBUGGING ---
            # Draw the text context that is being sent to audio
            cv2.putText(frame, display_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                        0.8, (0, 0, 255), 2, cv2.LINE_AA)
            
            # Show if muted
            if args.mute:
                cv2.putText(frame, "[MUTED]", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 
                            0.7, (0, 165, 255), 2, cv2.LINE_AA)

            cv2.imshow("Sound-Vision Debug Feed", frame)
            
            # Allow quit via 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("\nShutdown signal received.")
    finally:
        print("Cleaning up resources...")
        camera.release()
        cv2.destroyAllWindows()
        audio.queue_message("System shutting down.")
        time.sleep(1)

if __name__ == "__main__":
    main()

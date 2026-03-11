import time
import cv2
import argparse
import threading
import numpy as np
from camera_feed import CameraFeed
from detector import ObjectDetector
from context_engine import ContextEngine
from audio_engine import AudioEngine
from vlm_engine import VLMEngine

# Global state for VLM threading
vlm_thread = None
vlm_result_text = "Processing..."
vlm_last_latency_str = ""
vlm_is_busy = False
vlm_current_frame = None

def run_vlm_async(vlm_engine, frame_to_analyze, start_time, audio_engine):
    """Runs the VLM inference in a background thread."""
    global vlm_result_text, vlm_last_latency_str, vlm_is_busy
    try:
        # The VLM is slow. This blocks the thread, but NOT the main video loop
        vlm_text = vlm_engine.analyze_frame(frame_to_analyze)
        
        latency = time.time() - start_time
        vlm_last_latency_str = f"Latency: {latency:.2f}s"
        
        if vlm_text:
            vlm_result_text = vlm_text
            audio_engine.queue_message(vlm_result_text, priority="normal")
    finally:
        vlm_is_busy = False

def main():
    parser = argparse.ArgumentParser(description="Sound-Vision Assistive Workflow")
    parser.add_argument("--mute", action="store_true", help="Disable audio output (for office testing)")
    parser.add_argument("--engine", choices=["yolo", "vlm"], default="vlm", help="Select the vision engine to run (vlm or yolo)")
    
    # VLM specific arguments
    parser.add_argument("--vlm-url", type=str, help="Base URL for the VLM API (e.g. http://localhost:11434/v1 for Ollama)")
    parser.add_argument("--vlm-model", type=str, help="Model name for the VLM (e.g. llama3.2-vision or qwen-vl)")
    parser.add_argument("--vlm-key", type=str, help="API Key for the VLM (if using cloud provider)")
    
    args = parser.parse_args()

    print("Initializing Sound-Vision Assistive Workflow...")
    print(f"Engine: {args.engine.upper()}")
    print(f"Audio Output: {'MUTED' if args.mute else 'ENABLED'}")
    
    try:
        # Since VLM inference is now threaded, we can run the camera feed at full speed
        # so the visual debugging window doesn't look like a laggy slideshow.
        target_fps = 30
        camera = CameraFeed(source=0, target_fps=target_fps)
        audio = AudioEngine(throttle_seconds=3.0, muted=args.mute)
        
        # 2. Initialize Engine-Specific Components
        detector = None
        context_engine = None
        vlm_engine = None
        
        if args.engine == "yolo":
            detector = ObjectDetector(model_name="yolov8n.pt", target_classes=[0]) # 0 = Person
            context_engine = ContextEngine()
        else:
            # Pass environment variables down if provided via CLI
            import os
            if args.vlm_url: os.environ["VLM_BASE_URL"] = args.vlm_url
            if args.vlm_key: os.environ["VLM_API_KEY"] = args.vlm_key
            if args.vlm_model: os.environ["VLM_MODEL"] = args.vlm_model
            
            # This will pick up from the environment or use defaults
            vlm_engine = VLMEngine()

    except Exception as e:
        print(f"Failed to initialize components: {e}")
        return

    # 3. Wait for Heavy VLM Models to Download (Option A Fix)
    if args.engine == "vlm":
        import sys
        print("Ensuring VLM model is downloaded and ready (this takes a few minutes on first run)...")
        audio.queue_message("Connecting to AI vision model")
        
        sys.stdout.write("Waiting for model ")
        sys.stdout.flush()
        while not vlm_engine.is_model_ready():
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(5)
        print("\nVLM Model is ready!")

    print("Pipeline ready. Starting processing loop... Press 'q' in the video window to quit.")
    audio.queue_message(f"System Online. Running {args.engine} engine.")
    
    try:
        global vlm_result_text, vlm_last_latency_str, vlm_is_busy, vlm_thread, vlm_current_frame
        
        while True:
            # 1. Ingestion
            ret, frame = camera.get_frame()
            if not ret or frame is None:
                time.sleep(0.01)
                continue
                
            display_text = "Processing..."
            latency_str = ""
            start_time = time.time()
            
            # Decorator flags for the UI
            frame_analyzed_this_loop = False
            
            # The final image to show on screen
            canvas = frame.copy()
            
            # -----------------------------------------------------------------
            # PIPELINE: YOLO (Legacy Geometry-based)
            # -----------------------------------------------------------------
            if args.engine == "yolo":
                context_engine.frame_height, context_engine.frame_width = frame.shape[:2]
                detections = detector.detect(frame)
                
                # Draw boxes for debugging
                for det in detections:
                    x1, y1, x2, y2 = map(int, det["bbox"])
                    cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                if detections:
                    context = context_engine.process_detections(detections)
                    if context and context.get("text"):
                        display_text = context["text"]
                        
                        latency = time.time() - start_time
                        latency_str = f"Latency: {latency:.2f}s"
                        
                        # Only queue audio once processing is completely done
                        audio.queue_message(context["text"], priority=context.get("priority", "normal"))
                else:
                    display_text = "No person detected"

            # -----------------------------------------------------------------
            # PIPELINE: VLM (Semantic Meaning, Async Split-Screen Threaded)
            # -----------------------------------------------------------------
            elif args.engine == "vlm":
                display_text = vlm_result_text
                latency_str = vlm_last_latency_str
                
                # If the VLM is not currently thinking, grab THIS frame and send it off
                if not vlm_is_busy:
                    vlm_is_busy = True
                    frame_analyzed_this_loop = True
                    vlm_current_frame = frame.copy()
                    
                    vlm_thread = threading.Thread(
                        target=run_vlm_async, 
                        args=(vlm_engine, vlm_current_frame, start_time, audio)
                    )
                    vlm_thread.daemon = True
                    vlm_thread.start()

                # --- SPLIT SCREEN UI RENDERING ---
                # Left side: Live Feed. Right Side: What the AI is looking at right now
                # Resize both to fit side-by-side in the same window width (e.g. 640x480 -> 1280x480)
                
                live_side = frame.copy()
                ai_side = vlm_current_frame.copy() if vlm_current_frame is not None else frame.copy()
                
                # Draw borders
                if frame_analyzed_this_loop:
                    cv2.rectangle(live_side, (0, 0), (live_side.shape[1]-1, live_side.shape[0]-1), (0, 255, 0), 6)
                else:
                    cv2.rectangle(live_side, (0, 0), (live_side.shape[1]-1, live_side.shape[0]-1), (0, 0, 255), 2)
                    
                cv2.rectangle(ai_side, (0, 0), (ai_side.shape[1]-1, ai_side.shape[0]-1), (255, 255, 0), 4)

                cv2.putText(live_side, "LIVE FEED", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(ai_side, "AI VIEW", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
                
                # Stitch them side-by-side (horizontally)
                canvas = np.hstack((live_side, ai_side))

            # --- COMMON DEBUG OVERLAY ---
            # Draw the text context that is being sent to audio
            
            # To handle long VLM sentences, we might need to split it, but for now just slap it on screen
            # Draw on the bottom of the canvas
            text_size = cv2.getTextSize(display_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            cv2.rectangle(canvas, (0, canvas.shape[0] - 60), (canvas.shape[1], canvas.shape[0]), (0, 0, 0), -1) # Black banner behind text
            
            cv2.putText(canvas, display_text, (10, canvas.shape[0] - 35), cv2.FONT_HERSHEY_SIMPLEX, 
                        0.7, (255, 255, 255), 2, cv2.LINE_AA)
            
            # Draw latency telemetry
            if latency_str:
                cv2.putText(canvas, latency_str, (10, canvas.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                            0.6, (0, 255, 255), 2, cv2.LINE_AA)
            
            # Show if muted
            if args.mute:
                cv2.putText(canvas, "[MUTED]", (canvas.shape[1] - 120, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                            0.7, (0, 165, 255), 2, cv2.LINE_AA)

            cv2.imshow(f"Sound-Vision Debug Feed ({args.engine.upper()})", canvas)
            
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

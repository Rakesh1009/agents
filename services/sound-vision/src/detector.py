from ultralytics import YOLO

class ObjectDetector:
    """Wraps the Ultralytics YOLO model for object detection."""
    
    def __init__(self, model_name="yolov8n.pt", target_classes=[0]):
        # yolov8n is the nano model - fastest and smallest.
        print(f"Loading YOLO model: {model_name}")
        self.model = YOLO(model_name)
        
        # Target classes (0 is Person in COCO dataset)
        self.target_classes = target_classes

    def detect(self, frame):
        """Runs inference on a single frame and filters for target classes."""
        # Run YOLO inference
        results = self.model(frame, verbose=False)[0]
        
        detections = []
        for box in results.boxes:
            class_id = int(box.cls[0].item())
            confidence = box.conf[0].item()
            
            # Only keep detections of our target classes
            if class_id in self.target_classes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                
                detections.append({
                    "class_id": class_id,
                    "confidence": confidence,
                    "bbox": [x1, y1, x2, y2]
                })
                
        return detections

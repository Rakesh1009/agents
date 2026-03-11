class ContextEngine:
    """Translates raw bounding box data into spatial context strings."""
    
    def __init__(self, frame_width=640, frame_height=480):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.total_area = frame_width * frame_height

    def process_detections(self, detections):
        """
        Takes a list of detections and generates a prioritized textual description.
        Prioritizes the closest (largest) object.
        """
        if not detections:
            return None
            
        # Find the largest bounding box (heuristic for closest)
        largest_det = None
        max_area = 0
        
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            area = (x2 - x1) * (y2 - y1)
            
            if area > max_area:
                max_area = area
                largest_det = det
                
        if not largest_det:
            return None
            
        # 1. Calculate Proximity
        area_ratio = max_area / self.total_area
        
        if area_ratio > 0.40:
            proximity = "very close"
            priority = "urgent"
        elif area_ratio > 0.15:
            proximity = "nearby"
            priority = "high"
        else:
            proximity = "in the distance"
            priority = "normal"
            
        # 2. Calculate Position (Left, Center, Right)
        x1, _, x2, _ = largest_det["bbox"]
        center_x = (x1 + x2) / 2
        
        # Split screen into thirds
        third = self.frame_width / 3
        if center_x < third:
            position = "on the left"
        elif center_x > (2 * third):
            position = "on the right"
        else:
            position = "in front of you"
            
        text = f"Person {proximity} {position}."
        
        return {
            "text": text,
            "priority": priority,
            "raw": largest_det
        }

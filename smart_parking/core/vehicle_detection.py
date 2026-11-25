"""YOLO vehicle detection wrapper. Handles model loading and inference."""
import os
import cv2
from ultralytics import YOLO

# The classes we care about in COCO dataset
VEHICLE_CLASSES = {
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck"
}

# Distinct colors for bounding boxes (BGR format)
CLASS_COLORS = {
    2: (19, 168, 158),  # Teal (Car)
    3: (240, 164, 58),  # Orange (Motorcycle)
    5: (34, 160, 107),  # Emerald (Bus)
    7: (220, 84, 84)    # Red (Truck)
}


class VehicleDetector:
    def __init__(self, model_path="models/yolov8n.pt", conf_threshold=0.4):
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.model = None
        self.error = None
        self._load_model()

    def _load_model(self):
        if not os.path.exists(self.model_path):
            self.error = f"Model not found at {self.model_path}. Download it first."
            return
        try:
            self.model = YOLO(self.model_path)
        except Exception as e:
            self.error = f"Failed to load model: {e}"

    def is_ready(self):
        return self.model is not None

    def detect(self, frame):
        """
        Runs inference on a BGR frame.
        Returns: (annotated_frame, list_of_detections)
        detections: [{"class_id": 2, "class_name": "Car", "confidence": 0.89, "bbox": (x1,y1,x2,y2)}]
        """
        if not self.is_ready() or frame is None:
            return frame, []

        # Run YOLO inference
        results = self.model(frame, verbose=False, conf=self.conf_threshold)[0]
        
        annotated = frame.copy()
        detections = []

        for box in results.boxes:
            cls_id = int(box.cls[0].item())
            
            # Filter out non-vehicles
            if cls_id not in VEHICLE_CLASSES:
                continue

            conf = float(box.conf[0].item())
            # Bounding box coordinates (top-left, bottom-right)
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            
            detections.append({
                "class_id": cls_id,
                "class_name": VEHICLE_CLASSES[cls_id],
                "confidence": conf,
                "bbox": (x1, y1, x2, y2)
            })

            # Draw bounding box
            color = CLASS_COLORS.get(cls_id, (255, 255, 255))
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            # Draw label background
            label = f"{VEHICLE_CLASSES[cls_id]} {conf:.2f}"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - 20), (x1 + w, y1), color, -1)
            
            # Draw label text
            cv2.putText(annotated, label, (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

        return annotated, detections
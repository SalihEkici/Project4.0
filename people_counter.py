from ultralytics import YOLO
import cv2

model = YOLO("YOLOv8n.pt")


results = model.predict(source="0", show=True, classes=[0])

print(results)

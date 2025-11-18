import cv2
import numpy as np
from ultralytics import YOLO

#loading yolo to detect the avg number of people in the video
MODEL = YOLO('yolov8n.pt')

def average_people_in_video(video_path, frame_skip=3):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError('Could not open video: ' + video_path)

    frame_idx = 0
    total_people = 0
    sampled = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        if frame_idx % frame_skip != 0:
            continue

        results = MODEL(frame)
        boxes = results[0].boxes
        count = 0
        for box in boxes:
            cls = int(box.cls.cpu().numpy())
            name = MODEL.model.names.get(cls) if hasattr(MODEL.model, 'names') else str(cls)
            if name == 'person':
                count += 1
        total_people += count
        sampled += 1

    cap.release()
    if sampled == 0:
        return 0.0
    return float(total_people) / sampled

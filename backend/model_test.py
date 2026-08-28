from ultralytics import YOLO

print("[1] Loading model...")

model = YOLO("best.pt")

print("[2] Model loaded successfully!")

print("[3] Model task:", model.task)
print("[4] Model names:", model.names)

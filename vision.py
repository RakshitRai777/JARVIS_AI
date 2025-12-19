import cv2
from logger import info, error

def capture_image(path="vision.jpg"):
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    cam.release()

    if not ret:
        error("Camera capture failed")
        return None

    cv2.imwrite(path, frame)
    info(f"Image captured: {path}")
    return path

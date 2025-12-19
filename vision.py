import cv2


def capture_image(path="vision.jpg"):
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    cam.release()

    if not ret:
        return None

    cv2.imwrite(path, frame)
    return path

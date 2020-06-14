import cv2
import asyncio


async def detect(conf, frame, detector):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    rects = detector.detectMultiScale(gray, scaleFactor=1.05,
	                              minNeighbors=9, minSize=(30, 30),
	                              flags=cv2.CASCADE_SCALE_IMAGE)

    # check to see if a face was found
    if len(rects) > 0:
        return frame

    return None


from imutils.video import VideoStream
import imutils
import time
import cv2
import easygopigo3 as easy

from vision import QRCodeScanner


gopigo3 = easy.EasyGoPiGo3()

print("[INFO] warming up camera...")
vs = VideoStream(usePiCamera=1).start()
time.sleep(2.0)


def main():
    scanner = QRCodeScanner()

    while True:
        # grab the frame from the threaded video stream and resize it to
        # have a maximum width of 400 pixels
        frame = vs.read()
        frame = imutils.resize(frame, width=400)

        qrcode = scanner.process(frame)
        if qrcode == "LEFT":
            gopigo3.left()
        elif qrcode == "RIGHT":
            gopigo3.right()
        elif qrcode == "BACK":
            gopigo3.drive_degrees(180)

        cv2.imshow("Camera", frame)

        # if the `q` key was pressed, break from the loop
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break


if __name__ == "__main__":
    try:
        main()
    except IOError as error:
        # if the GoPiGo3 is not reachable
        # then print the error and exit
        print(str(error))
        exit(1)

    finally:
        print("[INFO] cleaning up...")
        cv2.destroyAllWindows()
        vs.stop()
        gopigo3.stop()

    exit(0)

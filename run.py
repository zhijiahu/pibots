
from imutils.video import VideoStream
import imutils
import time
import cv2

from vision import QRCodeScanner


def main():
    scanner = QRCodeScanner()

    while True:
        # grab the frame from the threaded video stream and resize it to
        # have a maximum width of 400 pixels
        frame = vs.read()
        frame = imutils.resize(frame, width=400)

        scanner.process(frame)

        cv2.imshow("Camera", frame)

        # if the `q` key was pressed, break from the loop
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break


if __name__ == "__main__":
    try:
        print("[INFO] warming up camera...")
        vs = VideoStream(usePiCamera=0).start()
        time.sleep(2.0)

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

    exit(0)

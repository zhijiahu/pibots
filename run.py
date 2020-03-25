
from imutils.video import VideoStream
import imutils
import datetime
import time
import threading
import argparse
import cv2
import easygopigo3 as easy
from flask import Response
from flask import Flask
from flask import render_template

from vision import QRCodeScanner


gopigo3 = easy.EasyGoPiGo3()

# initialize the output frame and a lock used to ensure thread-safe
# exchanges of the output frames (useful for multiple browsers/tabs
# are viewing tthe stream)
outputFrame = None
lock = threading.Lock()

# initialize a flask object
app = Flask(__name__)

print("[INFO] warming up camera...")
vs = VideoStream(usePiCamera=1).start()
time.sleep(2.0)

@app.route("/")
def index():
        # return the rendered template
        return render_template("index.html")

def main():
        global vs, outputFrame, lock

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

                timestamp = datetime.datetime.now()
                cv2.putText(frame, timestamp.strftime("%A %d %B %Y %I:%M:%S%p"),
                            (10, frame.shape[0] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0,0,255), 1)

                # acquire the lock, set the output frame, and release the
                # lock
                with lock:
                        outputFrame = frame.copy()

                # if the `q` key was pressed, break from the loop
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                        break

def generate():
        # grab global references to the output frame and lock variables
        global outputFrame, lock

        # loop over frames from the output stream
        while True:
                # wait until the lock is acquired
                with lock:
                        # check if the output frame is available, otherwise skip
                        # the iteration of the loop
                        if outputFrame is None:
                                continue

                        # encode the frame in JPEG format
                        (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)

                        # ensure the frame was successfully encoded
                        if not flag:
                                continue

                # yield the output frame in the byte format
                yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')

@app.route("/video_feed")
def video_feed():
        # return the response generated along with the specific media
        # type (mime type)
        return Response(generate(),
                        mimetype = "multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    try:
            ap = argparse.ArgumentParser()
            ap.add_argument("-i", "--ip", type=str, required=True,
                            help="ip address of the device")
            ap.add_argument("-o", "--port", type=int, required=True,
                            help="ephemeral port number of the server (1024 to 65535)")
            args = vars(ap.parse_args())

            # start a thread that will start the logic for the car
            t = threading.Thread(target=main, args=())
            t.daemon = True
            t.start()

            # start the flask app that listens for remote commands
            app.run(host=args["ip"], port=args["port"], debug=True,
                    threaded=True, use_reloader=False)

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

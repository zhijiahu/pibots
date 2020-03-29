
from imutils.video import VideoStream
from multiprocessing import Manager
from multiprocessing import Process
import imutils
import datetime
import time
import threading
import signal
import argparse
import cv2
import easygopigo3
import sys
from flask import Response
from flask import Flask
from flask import render_template

from vision import QRCodeScanner
from vision.objcenter import ObjCenter

# set the max wheel speed constant which should be tuned based on
# your driving surface and available battery voltage
WHEEL_SPEED_CONSTANT = 30

# initialize the output frame and a lock used to ensure thread-safe
# exchanges of the output frames (useful for multiple browsers/tabs
# are viewing tthe stream)
outputFrame = None
lock = threading.Lock()

# initialize a flask object
app = Flask(__name__)


# signal trap to handle keyboard interrupt
def signal_handler(sig, frame):

    # print a status message and reset
    print("[INFO] You pressed `ctrl + c`! Resetting your GoPiGo3...")
    gpg = easygopigo3.EasyGoPiGo3()
    gpg.reset_all()
    sys.exit()


def scan(args, objX, objY, search, lPower, rPower, powerDuration):
    global vs, outputFrame, lock

    t = threading.Thread(target=remote_feed, args=(args, ))
    t.daemon = True
    t.start()

    print('[INFO] warming up camera...')
    vs = VideoStream(usePiCamera=1).start()
    time.sleep(2.0)

    # instantiate scanners
    obj = ObjCenter(args)
    scanner = QRCodeScanner(args)

    while True:

        # grab the frame from the threaded video stream and resize it to
        # have a maximum width of 400 pixels
        frame = vs.read()
        frame = imutils.resize(frame, width=400)

        # find the object's location
        combined = []
        m = obj.update(frame)
        if m is not None:
            combined.append(m)

        m = scanner.update(frame)
        if m is not None:
            combined.append(m)

        if combined:
            multipliers = [sum(x) / len(combined) for x in zip(*combined)]
        else:
            multipliers = None

        # begin searching for the object if it is not found
        if multipliers == None:
            search.value = 1
            cv2.putText(
                frame,
                'searching...',
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 0xFF),
                2,
                )
        else:
            # otherwise set the motor power
            search.value = 0
            (lMultiplier, rMultiplier, duration) = multipliers
            lPower.value = int(WHEEL_SPEED_CONSTANT * lMultiplier)
            rPower.value = int(WHEEL_SPEED_CONSTANT * rMultiplier)
            powerDuration.value = int(duration)

            cv2.putText(
                frame,
                'tracking...',
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0xFF, 0),
                2,
                )

        timestamp = datetime.datetime.now()
        cv2.putText(
            frame,
            timestamp.strftime('%A %d %B %Y %I:%M:%S%p'),
            (10, frame.shape[0] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.35,
            (0, 0, 0xFF),
            1,
            )

        # acquire the lock, set the output frame, and release the
        # lock
        with lock:
            outputFrame = frame.copy()

        # if the `q` key was pressed, break from the loop
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    # release the file pointers
    print('[INFO] cleaning up...')
    vs.stop()


def go(lPower, rPower, powerDuration, search):
    # signal trap to handle keyboard interrupt
    signal.signal(signal.SIGINT, signal_handler)

    # create the easygopigo3 object
    gpg = easygopigo3.EasyGoPiGo3()
    time.sleep(5)

    # loop indefinitely
    while True:

        # check if we are performing a search
        if search.value == 1:
            # set the wheel speed
            gpg.set_motor_power(gpg.MOTOR_LEFT, WHEEL_SPEED_CONSTANT)
            gpg.set_motor_power(gpg.MOTOR_RIGHT, WHEEL_SPEED_CONSTANT)
        else:

            # otherwise, we have detected the object
            # set the wheel speed
            gpg.set_motor_power(gpg.MOTOR_LEFT, lPower.value)
            gpg.set_motor_power(gpg.MOTOR_RIGHT, rPower.value)
            if powerDuration.value > 0:
                time.sleep(powerDuration.value)

    # reset the GoPiGo3
    gpg.reset_all()


def remote_feed(args):
    # start the flask app that listens for remote commands
    app.run(host=args['ip'], port=args['port'], debug=True,
            threaded=True, use_reloader=False)


@app.route('/')
def index():
    # return the rendered template
    return render_template('index.html')


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
            (flag, encodedImage) = cv2.imencode('.jpg', outputFrame)

            # ensure the frame was successfully encoded
            if not flag:
                continue

            # yield the output frame in the byte format
            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')


@app.route('/video_feed')
def video_feed():
    # return the response generated along with the specific media
    # type (mime type)
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame'
                    )

if __name__ == '__main__':
    # start a manager for managing process-safe variables
    with Manager() as manager:

        # construct the argument parser and parse the arguments
        ap = argparse.ArgumentParser()

        ap.add_argument('--ip', type=str, default='0.0.0.0',
                        help='ip address of the device')
        ap.add_argument('--port', type=int, default=5000,
                        help='ephemeral port number of the server (1024 to 65535)')
        ap.add_argument('-o', '--object', required=True,
                        help='type of object the gopigo should drive to')
        ap.add_argument('-p', '--prototxt',
                        help="path to Caffe 'deploy' prototxt file")
        ap.add_argument('-m', '--model',
                        help='path to Caffe pre-trained model')
        ap.add_argument('-c', '--confidence', type=float, default=0.4,
                        help='minimum probability to filter weak detections')
        ap.add_argument('-s', '--size', type=int, default=10,
                        help='size of the deque')
        args = manager.dict(vars(ap.parse_args()))

        # set integer values for the object's (x, y)-coordinates
        objX = manager.Value('i', 0)
        objY = manager.Value('i', 0)

        # initialize our left and right motor speeds
        lPower = manager.Value('i', 0)
        rPower = manager.Value('i', 0)
        powerDuration = manager.Value('i', 0)

        # initalize a boolean which indicates if we are currently
        # searching for an object (i.e. spinning in place)
        search = manager.Value('i', 0)

        # we have 3 independent processes
        # 1. scan   -   searches environment and calulcates motor values
        #               based on detected object's position
        # 2. go       - drives the motors
        objectProcess = Process(target=scan, args=(
            args,
            objX,
            objY,
            search,
            lPower,
            rPower,
            powerDuration
        ))
        goProcess = Process(target=go, args=(lPower, rPower, powerDuration, search))

        # signal trap to handle keyboard interrupt
        signal.signal(signal.SIGINT, signal_handler)

        # start all 2 processes
        objectProcess.start()
        goProcess.start()

        # join all 2 processes
        objectProcess.join()
        goProcess.join()

        # create a new GoPiGo3 object and reset the GoPiGo3
        gpg = easygopigo3.EasyGoPiGo3()
        gpg.reset_all()

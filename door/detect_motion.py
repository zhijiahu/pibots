
from utils import Conf
from imutils.video import VideoStream
from pyHS100 import SmartPlug
import imagezmq
import socket
import numpy as np
import argparse
import datetime
import imutils
import signal
import time
import sys
import cv2
import os

def signal_handler(sig, frame):
    # show message to user
    print("\n[INFO] You pressed `ctrl + c`!")

    # gracefully exist
    sys.exit(0)

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--conf", required=True,
                help="path to the JSON configuration file")
args = vars(ap.parse_args())

# load our configuration settings
conf = Conf(args["conf"])

vs = VideoStream(usePiCamera=conf["picamera"]).start()
time.sleep(3.0)

# OpenCV background subtractors
OPENCV_BG_SUBTRACTORS = {
    "CNT": cv2.bgsegm.createBackgroundSubtractorCNT,
    "GMG": cv2.bgsegm.createBackgroundSubtractorGMG,
    "MOG": cv2.bgsegm.createBackgroundSubtractorMOG,
    "GSOC": cv2.bgsegm.createBackgroundSubtractorGSOC,
    "LSBP": cv2.bgsegm.createBackgroundSubtractorLSBP
}

# create our background subtractor
fgbg = OPENCV_BG_SUBTRACTORS[conf["bg_sub"]]()

# create erosion and dilation kernels
eKernel = np.ones(tuple(conf["erode"]["kernel"]), "uint8")
dKernel = np.ones(tuple(conf["dilate"]["kernel"]), "uint8")
frame_count = 0

# initialize the ImageSender object with the socket address of the
# server
sender = imagezmq.ImageSender(connect_to = 'tcp://*:5566', REQ_REP = False)
#sender = imagezmq.ImageSender(connect_to = 'tcp://{}:5555'.format(conf['server_ip']))
rpiName = socket.gethostname()
send_time = None

try:
    light_plug = SmartPlug(conf["ip_of_plug"])
    light_plug.turn_off()
except Exception:
    pass

# begin capturing "ctrl + c" signals
signal.signal(signal.SIGINT, signal_handler)
print("[INFO] detecting motion and sending those frames to another RPi.")

# loop through the frames
while True:
    # grab a frame from the video stream
    frame = vs.read()

    timenow = datetime.datetime.now()

    # check to see if should send the frame
    if send_time is not None:
        if (timenow - send_time).seconds <= conf["send_interval"]:
            print("Broadcasting image on *:5566")
            #print("Sending image from {} to {}".format(rpiName, conf["server_ip"]))
            sender.send_image(rpiName, frame)
            continue
        else:
            try:
                light_plug.turn_off()
                print("Turning light off")
            except Exception:
                pass

            send_time = None
            frame_count = 0

    frame_count += 1

    # resize the frame apply the background subtractor to generate
    # motion mask
    mask = fgbg.apply(frame)

    # Make sure the BG substractor buffer is applied from at least the buffer size
    if frame_count < conf['frame_buffer_size']:
        continue

    # perform erosions and dilations to eliminate noise and fill gaps
    mask = cv2.erode(mask, eKernel,
                     iterations=conf["erode"]["iterations"])
    mask = cv2.dilate(mask, dKernel,
                      iterations=conf["dilate"]["iterations"])

    # find contours in the mask and reset the motion status
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    # loop over the contours to check for motion
    detectedMotion = False
    for c in cnts:
        # compute the bounding circle and rectangle for the contour
        ((x, y), radius) = cv2.minEnclosingCircle(c)
        (rx, ry, rw, rh) = cv2.boundingRect(c)

        # convert floating point values to integers
        (x, y, radius) = [int(v) for v in (x, y, radius)]

        # only process motion contours above the specified size
        if radius >= conf["min_radius"]:
            detectedMotion = True
            break

    # motion detected, start sending frames over
    if detectedMotion:
        send_time = timenow
        try:
            light_plug.turn_on()
            print("Turning light on")
        except Exception:
            pass

    # check to see if we're displaying the frame to our screen
    if conf["display"]:
        # display the frame and grab keypresses
        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF

        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break

# stop the video stream
vs.stop()

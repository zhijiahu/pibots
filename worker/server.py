
import asyncio
import os
import argparse
import imagezmq
import imutils
import cv2
from utils import Conf
from redis import Redis
from rq import Queue
import numpy as np
from datetime import datetime
import socket

from tasks import detect_person
from tasks import detect_face

from parseyolooutput import ParseYOLOOutput

frame = None
rpiName = "unknown"

async def main():
    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--conf", required=True,
                    help="Path to the input configuration file")
    args = vars(ap.parse_args())

    # load the configuration file and label encoder
    conf = Conf(args["conf"])
    
    await asyncio.gather(read_frame(), process_frame(conf))

    cv2.destroyAllWindows()

async def read_frame():
    global frame
    global rpiName

    imageHub = imagezmq.ImageHub(open_port='tcp://172.16.0.100:5566', REQ_REP=False)

    print("[INFO] Waiting for frames ...")
    while True:
        (rpiName, image) = imageHub.recv_image()
        if image is None:
            continue

        print("[INFO] Received a a frame in socket")
        frame = image

        # Empty the recv buffer
        while True:
            (rpiName, image) = imageHub.recv_image()
            if image is None:
                break

        await asyncio.sleep(0) # give control to processing task

async def process_frame(conf):
    global frame
    global rpiName

    if conf["detector"] == "yolo":
        # init redis and rq
        q = Queue(connection=Redis())

        labelsPath = os.path.sep.join([conf["yolo_path"], "coco.names"])
        LABELS = open(labelsPath).read().strip().split("\n")

        # initialize a list of colors to represent each possible class label
        np.random.seed(42)
        COLORS = np.random.randint(0, 255, size=(len(LABELS), 3),
                                   dtype="uint8")

        # derive the paths to the YOLO weights and model configuration
        weightsPath = os.path.sep.join([conf["yolo_path"], "yolov3.weights"])
        configPath = os.path.sep.join([conf["yolo_path"], "yolov3.cfg"])

        # load our YOLO object detector trained on COCO dataset (80 classes)
        # and determine only the *output* layer names that we need from YOLO
        print("[INFO] Loading YOLO from disk...")
        net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)
        #net.setPreferableTarget(cv2.dnn.DNN_TARGET_MYRIAD)
        ln = net.getLayerNames()
        ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]

        # initialize the YOLO output parsing object
        pyo = ParseYOLOOutput(conf)

    elif conf["detector"] == "haarcascade":
        haarcascade_detector = cv2.CascadeClassifier(conf['haarPath'])

    # initialize the imagezmq
    imageSender = imagezmq.ImageSender(connect_to='tcp://*:5577', REQ_REP = False)

    print("[INFO] Ready to process frame")

    while True:
        # resize the frame to have a maximum width of 400 pixels
        frame = imutils.resize(frame, width=400)

        if conf['detector'] == "yolo":
            detected_frame = await detect_person(conf, frame, pyo, net, ln, LABELS, COLORS)
        elif conf['detector'] == "haarcascade":
            detected_frame = await detect_face(conf, frame, haarcascade_detector)

        if detected_frame is not None:
            imageSender.send_image(socket.gethostname(), detected_frame)
            print("[INFO] Sending detected frame to gopigo")
        else:
            print("[INFO] Nothing detected in frame")

        await asyncio.sleep(0)

        key = cv2.waitKey(1) & 0xFF
        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break


if __name__ == '__main__':
    asyncio.run(main())




from collections import deque
from collections import namedtuple
import numpy as np
import imutils
import cv2

from .sensorbase import SensorBase


class ObjCenterSSD(SensorBase):
    def __init__(self, args):
        super(ObjCenterSSD, self).__init__(args)

        # set instance variables
        self.objType = args["object"]

        # initialize the list of class labels MobileNet SSD was
        # trained to detect, then generate a set of bounding box
        # colors for each class
        self.CLASSES = ["background", "aeroplane", "bicycle", "bird",
            "boat", "bottle", "bus", "car", "cat", "chair", "cow",
            "diningtable", "dog", "horse", "motorbike", "person",
            "pottedplant", "sheep", "sofa", "train", "tvmonitor"]
        self.COLORS = np.random.uniform(0, 255,
            size=(len(self.CLASSES), 3))

        # check if the object type is a part of class labels
        # MobileNet SDD was trained to detect
        if self.objType in self.CLASSES:
            # load our serialized model from disk
            print("[INFO] loading model...")
            self.net = cv2.dnn.readNetFromCaffe(args["prototxt"],
                args["model"])
            self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_MYRIAD)

        # otherwise, alert the user regarding this and stop the
        # application
        else:
            print("[ERROR] object type not part of class labels" \
                " model was trained on...")
            exit(0)

    def update_internal(self, frame):
        # grab the frame dimensions and convert it to a blob
        (h, w) = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)),
            0.007843, (300, 300), 127.5)

        # pass the blob through the network and obtain the detections
        # and predictions
        self.net.setInput(blob)
        detections = self.net.forward()

        # loop over the detections
        for i in np.arange(0, detections.shape[2]):
            # extract the confidence (i.e., probability) associated
            # with the prediction
            confidence = detections[0, 0, i, 2]

            # filter out weak detections by ensuring the `confidence`
            # is greater than the minimum confidence
            if confidence > self.args["confidence"]:
                # extract the index of the class label from the
                # `detections`
                idx = int(detections[0, 0, i, 1])

                # filter for only object type we are interested in
                if self.CLASSES[idx] != self.objType:
                    continue

                # compute the (x, y)-coordinates of the bounding
                # box for the object
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")

                # draw the prediction on the frame
                label = "{}: {:.2f}%".format(self.CLASSES[idx],
                    confidence * 100)
                cv2.rectangle(frame, (startX, startY), (endX, endY),
                    self.COLORS[idx], 2)

                # calculate the center (x, y)-coordinates and width
                # of the object
                objX = int((endX - startX / 2) + startX)
                objY = int((endY - startY / 2) + startY)
                width = endX - startX

                # when the object is on the left, the robot needs to
                # veer left until the next update
                if objX < w // 2:
                    self.l_multiplier = 0.50
                    self.r_multiplier = 1.50

                # when the object is on the right, the robot should
                # veer right until the next update
                elif objX > w // 2:
                    self.l_multiplier = 1.50
                    self.r_multiplier = 0.50

                # otherwise, the object is in the center, so the robot
                # should go straight until the next update
                else:
                    self.l_multiplier = 0.9
                    self.r_multiplier = 0.9

                self.motor_duration = 0
                print("[INFO] Detected object")

                return True

        return False

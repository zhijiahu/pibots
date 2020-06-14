
from collections import deque
from collections import namedtuple
import numpy as np
import imutils
import cv2
import os

from .parseyolooutput import ParseYOLOOutput
from .sensorbase import SensorBase


class ObjCenterYolo(SensorBase):
    def __init__(self, conf):
        super(ObjCenterYolo, self).__init__(conf)

        # load the COCO class labels our YOLO model was trained on
        labelsPath = os.path.sep.join([conf["yolo_path"], "coco.names"])
        self.LABELS = open(labelsPath).read().strip().split("\n")

        # initialize a list of colors to represent each possible class label
        np.random.seed(42)
        self.COLORS = np.random.randint(0, 255, size=(len(self.LABELS), 3),
	                                dtype="uint8")

        # derive the paths to the YOLO weights and model configuration
        weightsPath = os.path.sep.join([conf["yolo_path"], "yolov3.weights"])
        configPath = os.path.sep.join([conf["yolo_path"], "yolov3.cfg"])

        # load our YOLO object detector trained on COCO dataset (80 classes)
        # and determine only the *output* layer names that we need from YOLO
        print("[INFO] loading YOLO from disk...")
        self.net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)
        self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_MYRIAD)
        ln = self.net.getLayerNames()
        self.ln = [ln[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]

        self.W = None
        self.H = None

        # initialize the YOLO output parsing object
        self.pyo = ParseYOLOOutput(conf)

    def update_internal(self, frame):
        # if we do not already have the dimensions of the frame,
	# initialize it
        if self.H is None and self.W is None:
            (self.H, self.W) = frame.shape[:2]

        # construct a blob from the input frame and then perform
        # a forward pass of the YOLO object detector, giving us
        # our bounding boxes and associated probabilities
        blob = cv2.dnn.blobFromImage(frame, 1 / 255.0,
                                     (416, 416), swapRB=True, crop=False)
        self.net.setInput(blob)
        layerOutputs = self.net.forward(self.ln)

        # parse YOLOv3 output
        (boxes, confidences, classIDs) = self.pyo.parse(layerOutputs,
                                                        self.LABELS, self.H, self.W)

        # apply non-maxima suppression to suppress weak,
        # overlapping bounding boxes
        idxs = cv2.dnn.NMSBoxes(boxes, confidences,
                                self.args["confidence"], self.args["threshold"])

        # ensure at least one detection exists
        if len(idxs) > 0:
            # loop over the indexes we are keeping
            for i in idxs.flatten():
                # TODO: Detect multiple?
                detected_class = self.LABELS[classIDs[i]]

                # extract the bounding box coordinates
                (x, y) = (boxes[i][0], boxes[i][1])
                (w, h) = (boxes[i][2], boxes[i][3])

                # draw a bounding box rectangle and label on the frame
                color = [int(c) for c in self.COLORS[classIDs[i]]]
                cv2.rectangle(frame, (x, y), (x + w, y + h),
                              color, 2)
                text = "{}: {:.4f}".format(detected_class,
                                           confidences[i])
                y = (y - 15) if (y - 15) > 0 else h - 15
                cv2.putText(frame, text, (x, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                # when the object is on the left, the robot needs to
                # veer left until the next update
                if x < w // 2:
                    self.l_multiplier = 0.50
                    self.r_multiplier = 1.50

                # when the object is on the right, the robot should
                # veer right until the next update
                elif x > w // 2:
                    self.l_multiplier = 1.50
                    self.r_multiplier = 0.50

                # otherwise, the object is in the center, so the robot
                # should go straight until the next update
                else:
                    self.l_multiplier = 0.9
                    self.r_multiplier = 0.9

                self.motor_duration = 0

                print("[INFO] Detected {}".format(detected_class))
                os.system("mpg321 --stereo {}/{}.mp3".format(
                    self.args["msgs_path"], detected_class))

                return True

        return False

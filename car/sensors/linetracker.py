
from imutils.contours import sort_contours
import imutils
import cv2

from .sensorbase import SensorBase


class LineTracker(SensorBase):
    def __init__(self, args):
        super(LineTracker, self).__init__(args)

        # set the frame width
        self.width = 400

    def update_internal(self, frame):
        # resize the frame, convert to grayscale, and extract
        # dimensions
        frame = imutils.resize(frame, width=self.width)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        (H, W) = gray.shape

        # assuming the camera is aimed at a 45-deg down angle and
        # mounted on the top platform of the GoPiGo3, extract only the
        # region right in front of the camera
        startY = int(H * 0.80)
        endY = H
        startX = int(W * 0.20)
        endX = int(W * 0.80)
        roi = gray[startY:endY, startX:endX]

        # perform blurring to smooth the ROI
        blurred = cv2.GaussianBlur(roi, (5, 5), 0)

        # threshold the image
        (T, thresh) = cv2.threshold(blurred, 0, 255,
                                    cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        # apply a series of erosions to break apart connected
        # components and find contours in the mask
        eroded = cv2.erode(thresh, None, iterations=3)
        cnts = cv2.findContours(eroded.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        if not cnts:
            return False

        # sort contours left-to-right
        (cnts, boundingBoxes) = sort_contours(cnts,
                                              method="left-to-right")

        # a lack of contours indicates that no line is found, so we
        # should go straight (until the next update) at a 20% slower
        # rate by setting the multipliers to 80%
        if len(cnts) == 0:
            self.l_multiplier = 0.8
            self.r_multiplier = 0.8
            return True

        # determine the area on each side of the line (the first and
        # last contours)
        pixelsLeft = cv2.contourArea(cnts[0])
        pixelsRight = cv2.contourArea(cnts[-1])

        # when the line is on the left, the robot needs to veer left
        # until the next update
        if pixelsLeft < pixelsRight:
            self.l_multiplier = 0.60
            self.r_multiplier = 1.40

        # when the line is on the right, the robot should veer right
        # until the next update
        elif pixelsLeft > pixelsRight:
            self.l_multiplier = 1.40
            self.r_multiplier = 0.60

        # otherwise the areas are equal and the line is in the center,
        # so the robot should go straight until the next update
        else:
            self.l_multiplier = 0.9
            self.r_multiplier = 0.9

        # return the updated values
        return True

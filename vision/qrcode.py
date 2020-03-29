
from collections import deque
from pyzbar import pyzbar
import cv2


class QRCodeScanner:

    def __init__(self, args):
        self.args = args
        self.l_multiplier = None
        self.r_multiplier = None
        self.motor_duration = 0

        # initialize a deque which will be used to keep track of
        # successful detection made in last N frames
        self.history = deque(maxlen=args["size"])

    def update(self, frame):
        # find the barcodes in the frame and decode each of the barcodes
        qrcodes = pyzbar.decode(frame)

        if qrcodes:
            self.history.append(1)

            # Use the 1st detected qrcode
            qrcode = qrcodes[0]

            # extract the bounding box location of the qrcode and draw
            # the bounding box surrounding the qrcode on the image
            (x, y, w, h) = qrcode.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

            qrcode_data = qrcode.data.decode("utf-8")
            qrcode_type = qrcode.type

            # draw the qrcode data and qrcode type on the image
            text = "{}({})".format(qrcode_data, qrcode_type)
            cv2.putText(frame, text, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            print(text)

            if qrcode_data == "LEFT":
                self.r_multiplier = 0.0
                self.l_multiplier = 1.50
                self.motor_duration = 3
            elif qrcode_data == "RIGHT":
                self.r_multiplier = 1.50
                self.l_multiplier = 0.0
                self.motor_duration = 3
            elif qrcode_data == "BACK":
                self.r_multiplier = 0.0
                self.l_multiplier = 1.50
                self.motor_duration = 6
            else:
                return None

            return (self.l_multiplier, self.r_multiplier, self.motor_duration)

        # append 0 to the deque indicating no object of interest was
        # detected in this frame
        self.history.append(0)

        # check if any entry in the deque is set to 1 (indicating we
        # have been moving in the correct direction previously)
        if 1 in self.history:
            # check if both the multipliers are set to None, if so,
            # return no data
            if self.l_multiplier is None or self.r_multiplier is None:
                return None

            # otherwise, keep moving in the direction of previous
            # successful detection
            else:
                return (self.l_multiplier, self.r_multiplier, self.motor_duration)

        else:
            # otherwise return no data
            return None

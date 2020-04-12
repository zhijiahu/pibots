
from pyzbar import pyzbar
import cv2

from .sensorbase import SensorBase


class QRCodeScanner(SensorBase):

    def update_internal(self, frame):
        # find the barcodes in the frame and decode each of the barcodes
        qrcodes = pyzbar.decode(frame)
        if not qrcodes:
            return False

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
        turn_duration = 2.0
        turn_multiplier = 1.50

        if qrcode_data == "LEFT":
            self.r_multiplier = 0.0
            self.l_multiplier = turn_multiplier
            self.motor_duration = turn_duration
        elif qrcode_data == "RIGHT":
            self.r_multiplier = turn_multiplier
            self.l_multiplier = 0.0
            self.motor_duration = turn_duration
        elif qrcode_data == "BACK":
            self.r_multiplier = 0.0
            self.l_multiplier = turn_multiplier
            self.motor_duration = turn_duration * 2
        else:
            return False

        return True

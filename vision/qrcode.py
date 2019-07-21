
from pyzbar import pyzbar
import cv2


class QRCodeScanner:

    def __init__(self):
        pass

    def process(self, frame):
        # find the barcodes in the frame and decode each of the barcodes
        qrcodes = pyzbar.decode(frame)

        # loop over the detected qrcodes
        for qrcode in qrcodes:
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

            # return 1st one
            return qrcode_data

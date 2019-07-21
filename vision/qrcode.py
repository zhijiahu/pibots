
from pyzbar import pyzbar
import cv2


class QRCodeScanner:

    def __init__(self):
        self.found = set()

    def process(self, frame):
        # find the barcodes in the frame and decode each of the barcodes
        barcodes = pyzbar.decode(frame)

        # loop over the detected barcodes
        for barcode in barcodes:
            # extract the bounding box location of the barcode and draw
            # the bounding box surrounding the barcode on the image
            (x, y, w, h) = barcode.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

            barcode_data = barcode.data.decode("utf-8")
            barcode_type = barcode.type

            # TODO: Process

            # draw the barcode data and barcode type on the image
            text = "{} ({})".format(barcode_data, barcode_type)
            cv2.putText(frame, text, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            if barcode_data not in self.found:
                self.found.add(barcode_data)
                print(self.found)

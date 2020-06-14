
import os
import cv2
from math import cos, sin, pi, floor
from adafruit_rplidar import RPLidar
import threading
import random
from datetime import datetime
import glob

from .sensorbase import SensorBase


class ImageGatherer(SensorBase):

    def __init__(self, args):
        super(ImageGatherer, self).__init__(args)

        self.lidar = RPLidar(None, '/dev/ttyUSB0')
        self.scan_data = [0]*360
        self.snapshot_time = datetime.now()

        image_paths = glob.glob("{}/*.jpg".format(args["imageoutput"]))
        if image_paths:
            self.snapshot_count = max([int(os.path.splitext(path.split(os.path.sep)[-1])[0]) for path in image_paths])
        else:
            self.snapshot_count = 0

        print(self.lidar.info)
        print(self.lidar.health)

        t = threading.Thread(target=self._read_scans, args=())
        t.daemon = True
        t.start()

    def _read_scans(self):
        for scan in self.lidar.iter_scans():
            for (_, angle, distance) in scan:
                self.scan_data[min([359, floor(angle)])] = distance

    def update_internal(self, frame):

        # Capture a image
        now = datetime.now()
        if (now - self.snapshot_time).seconds > 5:
            self.snapshot_time = now

            # draw the timestamp on the frame
            ts = datetime.now().strftime("%A %d %B %Y %I:%M:%S%p")

            # write the current frame to output directory
            filename = "{}.jpg".format(str(self.snapshot_count).zfill(16))
            path = os.path.join(self.args["imageoutput"], filename)
            print("[INFO] Saving captured image to ", path)
            cv2.imwrite(path, frame)

            self.snapshot_count += 1

        r_multiplier = random.uniform(2.0, 3.0)
        l_multiplier = 1.0
        turn_duration = 2.0
        dist_to_obstacle = 300

        roi = self.scan_data[135:225]

        if any((dist > 0 and dist < dist_to_obstacle) for dist in roi):
            self.r_multiplier = r_multiplier if self.snapshot_count % 2 == 0 else l_multiplier
            self.l_multiplier = l_multiplier if self.snapshot_count % 2 == 0 else r_multiplier
            self.motor_duration = turn_duration
            print("[INFO] Avoiding obstacle!")
            return True

        return False

    def shutdown(self):
        print("[INFO] Stopping rplidar")
        self.lidar.stop()
        self.lidar.disconnect()

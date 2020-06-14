
import os
from math import cos, sin, pi, floor
from adafruit_rplidar import RPLidar
import threading
import random
from datetime import datetime

from .sensorbase import SensorBase


class RPLidarSensor(SensorBase):

    def __init__(self, args):
        super(RPLidarSensor, self).__init__(args)

        self.lidar = RPLidar(None, '/dev/ttyUSB0')
        self.scan_data = [0]*360
        self.time = datetime.now()
        self.count = 0

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

        now = datetime.now()
        if (now - self.time).seconds > 5:
            self.time = now
            self.count += 1

        r_multiplier = random.uniform(3.0, 5.0)
        l_multiplier = 1.0
        turn_duration = 2.0
        dist_to_obstacle = 350

        roi = self.scan_data[135:225]

        if any((dist > 0 and dist < dist_to_obstacle) for dist in roi):
            self.r_multiplier = r_multiplier if self.count % 2 == 0 else l_multiplier
            self.l_multiplier = l_multiplier if self.count % 2 == 0 else r_multiplier
            self.motor_duration = turn_duration
            print("[INFO] Avoiding obstacle!")
            return True

        return False

    def shutdown(self):
        print("[INFO] Stopping rplidar")
        self.lidar.stop()
        self.lidar.stop_motor()
        self.lidar.disconnect()

    def stop_motor(self):
        self.lidar.stop_motor()

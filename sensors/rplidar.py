
import os
from math import cos, sin, pi, floor
from adafruit_rplidar import RPLidar
import threading

from .sensorbase import SensorBase


class RPLidarSensor(SensorBase):

    def __init__(self, args):
        super(RPLidarSensor, self).__init__(args)

        self.lidar = RPLidar(None, '/dev/ttyUSB0')
        self.lidar.stop()

        self.scan_data = [0]*360

        print(self.lidar.info)

        t = threading.Thread(target=self._read_scans, args=())
        t.daemon = True
        t.start()

    def _read_scans(self):
        for scan in self.lidar.iter_scans():
            for (_, angle, distance) in scan:
                self.scan_data[min([359, floor(angle)])] = distance


    def update_internal(self, frame):

        turn_duration = 1.0
        turn_multiplier = 2.0
        dist_to_obstacle = 300

        roi = self.scan_data[135:225]

        if any((dist > 0 and dist < dist_to_obstacle) for dist in roi):
            self.r_multiplier = -turn_multiplier
            self.l_multiplier = -turn_multiplier
            self.motor_duration = turn_duration
            print("[INFO] Avoiding obstacle!")
            return True

        return False

    def shutdown(self):
        print("[INFO] Stopping rplidar")
        self.lidar.stop()
        self.lidar.disconnect()

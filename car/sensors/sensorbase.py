from collections import deque
import signal


class SensorBase:

    def __init__(self, args):
        self.args = args
        self.l_multiplier = None
        self.r_multiplier = None
        self.motor_duration = 0

        # initialize a deque which will be used to keep track of
        # successful detection made in last N frames
        self.history = deque(maxlen=args["size"])

    def update(self, frame):
        if self.update_internal(frame):
            self.history.append(1)
        else:
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

    def shutdown(self):
        pass

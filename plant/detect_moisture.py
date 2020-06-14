
import grovepi


class MoistureDetector:

    def __init__(self, port):
        self._port = port

    def read_moisture_value(self):
        moisture = grovepi.analogRead(self._port)
        print(moisture)

        condition = self._get_moisture_condition(moisture)
        print(condition)

        return (moisture, condition)

    def _get_moisture_condition(self, moisture_value):
        if moisture_value < 300:
            return "DRY"
        elif moisture_value < 700:
            return "HUMID"
        else:
            return "WET"

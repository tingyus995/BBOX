import time
import os
from gpiozero import DistanceSensor

class DoorDetection():
    def __init__(self):
        super().__init__()
        self.sensor = DistanceSensor(23, 24)
        self.opened = False
        self.flag_path = "/tmp/door_open"

    def _set_as_open(self):
        f = open(self.flag_path, "w")
        f.close()

    def _set_as_close(self):
        os.rmdir(self.flag_path)

    def run(self) -> None:
        while True:
            time.sleep(0.5)
            distance = self.sensor.value*100
            print("               " + str(distance) + "cm")
            #print('                 Distance to nearest object is ' +
            #         '{:1.2f} '.format(distance) + 'cm')
            newOpened = True if (distance > 37) else False

            if newOpened != self.opened:
                if newOpened:
                    self._set_as_open()
                else:
                    self._set_as_close()



program = DoorDetection()
program.run()

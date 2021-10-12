import threading
import time
from gpiozero import DistanceSensor

class DoorOpenEvent():
    pass

class DoorCloseEvent():
    pass

class DoorDetectionThread(threading.Thread):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.sensor = DistanceSensor(23, 24)
        self.opened = False

    def run(self) -> None:
        while not self.engine.should_stop:
            time.sleep(0.5)
            distance = self.sensor.value*100
            #print("               " + str(distance) + "cm")
            #print('                 Distance to nearest object is ' +
            #         '{:1.2f} '.format(distance) + 'cm')
            newOpened = True if (distance > 50) else False

            if newOpened != self.opened:
                self.opened = newOpened
                if self.opened:
                    self.engine.event_queue.put(DoorOpenEvent())
                else:
                    self.engine.event_queue.put(DoorCloseEvent())



import threading
import time

class TimerTimeoutEvent():
    pass

class Timer(threading.Thread):
    def __init__(self, engine, length, repeat = True):
        super().__init__()
        self.engine = engine
        self.length = length
        if self.length < 1:
            print("Minimum length hsould be 1 sec.")
            self.length = 1

        self.repeat = repeat

    def run(self) -> None:
        if self.repeat:
            while not self._should_stop():
                self._stoppable_timer()
        else:
            self._stoppable_timer()

    def _should_stop(self):
        return self.engine.should_stop

    def _stoppable_timer(self):
        for i in range(self.length):
            if self._should_stop():
                break
            time.sleep(1)
        self.engine.event_queue.put(TimerTimeoutEvent())
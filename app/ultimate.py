import threading
import time
import queue
import random

# all events coming from threads should go here
event_queue = queue.Queue()

should_stop = False

class DoorOpenEvent:
    pass
class DoorCloseEvent:
    pass

def door_detect():
    while not should_stop:
        time_to_next_open = random.randint(2, 10)
        time.sleep(time_to_next_open)
        event_queue.put(DoorOpenEvent())
        time_to_next_close = random.randint(2, 10)
        time.sleep(time_to_next_close)
        event_queue.put(DoorCloseEvent())
    print("door_detect stopped")

class TimerRang:
    pass

def scan_timer():
    while not should_stop:
        time.sleep(3)
        event_queue.put(TimerRang())
    print("scan timer stopped")

def shutdown_routine():
    print("Shutting down system...")
    global should_stop
    print(f"current should_stop: {should_stop}")
    should_stop = True
    print(f"current should_stop: {should_stop}")


def main():
    threads = []
    try:
        # start all threads
        door_detect_thread = threading.Thread(target=door_detect)
        threads.append(door_detect_thread)
        door_detect_thread.start()

        timer_thread = threading.Thread(target=scan_timer)
        threads.append(timer_thread)
        timer_thread.start()

        # find events from event loop
        while True:
            print("getting event")
            event = event_queue.get()
            print("got event")
            print(event)
    except KeyboardInterrupt:
        shutdown_routine()

main()



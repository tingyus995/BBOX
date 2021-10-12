from db import Container, ContainerDataThread
from animation import Breath, Chase, ClockwiseLoop, initial_fade, initial_thunder
from door import DoorCloseEvent, DoorDetectionThread, DoorOpenEvent
from scan import *
from timer import TimerTimeoutEvent, Timer
from gpiozero import LEDBoard
import queue
# firebase
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
# dht
import adafruit_dht

import cv2


class Engine:
    def __init__(self) -> None:
        # members
        self.event_queue = queue.Queue()
        self.should_stop = False
        self.should_stop_scanning = False

        # states
        self.door_is_open = False

        # initialize gpio
        self.pwmled = LEDBoard(2, 3, 4, 5, 6, 7, 8, 9,
                               10, 11, 12, 13, pwm=True)
        self.all_leds_off()

        # initialize dht
        self.dhtDevice = adafruit_dht.DHT11(25)

        # initialize database
        self.db = self.init_db()

        # initialize realtime listener
        self.initial_animation_name = "thunder"
        self.animation_name = "breath"
        self.listen_db()

        # initialize timer
        self.timer = Timer(self, 60 * 15, True)
        self.timer.start()

        # work around weird cv2 error
        self.cv2 = cv2

        # initialize threads
        self.door_detect_thread = DoorDetectionThread(self)
        self.door_detect_thread.start()

        self.animation_thread = None
        self.water_level_thread = None
        self.db_thread = None

        # pull events
        try:
            while True:
                print("waiting for event")
                event = self.event_queue.get()
                print(event)
                if isinstance(event, DoorOpenEvent):
                    self.door_is_open = True
                    self.should_stop_scanning = True
                    if self.water_level_thread is not None:
                        self.water_level_thread.join()
                        self.water_level_thread = None

                    # play animation when the door is opened
                    self.animation_thread = self._get_animation_thread()
                    self.animation_thread.start()
                    # send to cloud
                    if self.db_thread != None:
                        self.db_thread.join()
                    temperature, humidity = self.get_temperature_and_humidity()
                    self.db_thread = ContainerDataThread(
                        self, Container(True, temperature, humidity))
                    self.db_thread.start()
                elif isinstance(event, DoorCloseEvent):
                    self.door_is_open = False
                    print("stop called")
                    self.should_stop_scanning = False
                    self.animation_thread.stop()
                    print("joining")
                    self.animation_thread.join()
                    self.all_leds_off()

                    if self.db_thread != None:
                        self.db_thread.join()
                    temperature, humidity = self.get_temperature_and_humidity()
                    self.db_thread = ContainerDataThread(
                        self, Container(False, temperature, humidity))
                    self.db_thread.start()

                    self.water_level_thread = WaterLevelDetectionThread(self)
                    self.water_level_thread.start()
                elif isinstance(event, TimerTimeoutEvent):
                    # only update if the door is closed
                    if not self.door_is_open:
                        # update container info
                        if self.db_thread != None:
                            self.db_thread.join()
                        temperature, humidity = self.get_temperature_and_humidity()
                        print("got temperature")
                        self.db_thread = ContainerDataThread(
                            self, Container(False, temperature, humidity))
                        self.db_thread.start()
                        print("db thread started")

                        # update water level info
                        self.should_stop_scanning = True
                        if self.water_level_thread is not None:
                            self.water_level_thread.join()
                            self.water_level_thread = None
                        self.should_stop_scanning = False
                        print("checking water level thread")
                        self.water_level_thread = WaterLevelDetectionThread(
                            self)
                        print("water level thread started")
                        self.water_level_thread.start()

        except KeyboardInterrupt:
            print("[!] Shutdown requested by user")
            print("Shutting down all modules...")
            self.should_stop = True
            self.should_stop_scanning = True

            if self.animation_thread != None:
                self.animation_thread.stop()

            print("Shutting down dht device...")
            self.dhtDevice.exit()

    def all_leds_off(self):
        for led in self.pwmled:
            led.off()

    def init_db(self):
        # set up credential file
        cred = credentials.Certificate("/home/pi/Desktop/project/app.json")
        firebase_admin.initialize_app(cred)
        return firestore.client()

    def listen_db(self):

        def on_snapshot(doc_snapshot, changes, read_time):
            for doc in doc_snapshot:
                print(f'Received document snapshot: {doc.id}')
                container_data = doc.to_dict()
                self.initial_animation_name = container_data['initial_animation']
                self.animation_name = container_data['animation']
                # print(doc[u'initial_animation'])

        container_ref = self.db.collection(
            u'container').document(u'wVKFoTKN7Nfi0m662R7F')
        container_ref.on_snapshot(on_snapshot)

    def _get_animation_thread(self):
        # default initial animation
        initial_func = initial_fade

        if self.initial_animation_name.lower() == "fade":
            initial_func = initial_fade
        elif self.initial_animation_name.lower() == "thunder":
            initial_func = initial_thunder

        if self.animation_name.lower() == "clockwise":
            return ClockwiseLoop(self, initial_func)
        elif self.animation_name.lower() == "breath":
            return Breath(self, initial_func)
        elif self.animation_name.lower() == "chase":
            return Chase(self, initial_func)
        # default animation
        return Breath(self, initial_func)

    def get_temperature_and_humidity(self):
        while True:
            try:
                temperature_c = self.dhtDevice.temperature
                # temperature_f = temperature_c * (9 / 5) + 32
                humidity = self.dhtDevice.humidity
                print(
                    "Temp: {:.1f} C    Humidity: {}% ".format(
                        temperature_c, humidity
                    )
                )

                return temperature_c, humidity * 0.01
            except RuntimeError as error:
                # Errors happen fairly often, DHT's are hard to read, just keep going
                # print(error.args[0])
                print(
                    "[!] Failed to read temperature and humidity, try again in 1 secs.")
                time.sleep(1.0)
                continue
            except Exception as error:
                print(
                    "[!] Failed to read temperature and humidity, try again in 1 secs.")
                time.sleep(1.0)
                continue

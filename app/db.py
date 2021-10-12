import threading
import time


class Container:
    def __init__(self, opened, temperature, humidity):
        self.temperature = temperature
        self.opened = opened
        self.humidity = humidity



class ContainerDataThread(threading.Thread):
    def __init__(self, engine, container):
        super().__init__()
        self.engine = engine
        self.db = engine.db
        self.docId = "wVKFoTKN7Nfi0m662R7F"
        self.container = container

    def run(self) -> None:
        self.db.collection("container").document(self.docId).set({
            u'opened': self.container.opened,
            u'temperature': self.container.temperature,
            u'humidity': self.container.humidity
        },merge=True)
        print("Container upload done!")



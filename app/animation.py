import threading
import time



class AnimationThread(threading.Thread):
    def __init__(self, engine, initial = None):
        super().__init__()
        self.engine = engine
        self.pwmled = engine.pwmled
        self.should_stop = False
        self.initial = initial
        self.loop = True

    def run(self) -> None:
        if self.loop:
            self.play_initial()
            while not self.should_stop:
                self.animate()
        else:
            self.play_initial()
            self.animate()

    def play_initial(self):
        if self.initial is not None:
            self.initial(self.pwmled)
    def stop(self):
        self.should_stop = True


class ClockwiseLoop(AnimationThread):
    def __init__(self, engine, initial = None):
        super().__init__(engine, initial)

        self.seq = [8,6,4,2,0,1,3,5,7,9,10]
        self.pwmled[11].on()
        self.index = 0

    def animate(self) -> None:
        index0 = (self.index+0)%11
        index1 = (self.index+1)%11
        index2 = (self.index+2)%11
        index3 = (self.index+3)%11
        index4 = (self.index+4)%11
        index5 = (self.index+5)%11
        index6 = (self.index+6)%11
        self.pwmled[self.seq[index0]].value = 0.125
        self.pwmled[self.seq[index1]].value = 0.25
        self.pwmled[self.seq[index2]].value = 0.5
        self.pwmled[self.seq[index3]].value = 1
        self.pwmled[self.seq[index4]].value = 0.5
        self.pwmled[self.seq[index5]].value = 0.25
        self.pwmled[self.seq[index6]].value = 0.125
        if self.should_stop:
                return
        time.sleep(0.1)
        self.pwmled[self.seq[index0]].value = 0
        self.index+=1
        if(self.index%11==0):
            self.index=0
        print(self.index)

class Chase(AnimationThread):
    def __init__(self, engine, initial = None):
        super().__init__(engine, initial)

        self.seq = [10,9,7,5,3,1,0,2,4,6,8]


    def animate(self) -> None:
        count = 11
        for t in range(10,-1,-1):

            for i in range(count):
                self.pwmled[self.seq[i]].on()
                time.sleep(0.07)

                if(i!=t):
                    self.pwmled[self.seq[i]].off()
            count-=1
            print(i,count)
            if self.should_stop:
                return

class Breath(AnimationThread):
    def __init__(self, engine, initial = None):
        super().__init__(engine, initial)

    def animate(self) -> None:
        for i in range(10,100,5):
            for led in self.pwmled:
                led.value = i/100
            if self.should_stop:
                return
            time.sleep(0.1)

        for i in range(100, 10,-5):

            for led in self.pwmled:
                led.value = i/100
            if self.should_stop:
                return
            time.sleep(0.1)


# initial animations
def initial_fade(pwmled):
    for i in range(0, 100, 5):
        for led in pwmled:
            led.value = i/150
        time.sleep(0.1)

def initial_thunder(pwmled):
    seq = [8,6,4,2,0,1,3,5,7,9,10]
    for _ in range(2):
        for s in seq:
            pwmled[s].on()
            time.sleep(0.05)
            pwmled[s].off()

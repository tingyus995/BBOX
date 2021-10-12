import threading
import time
import datetime

import os
import numpy as np
from firebase_admin import firestore
#import self.cv2


class Bottle:
    def __init__(self, id, percent_left):
        self.id = id
        self.percent_left = percent_left
        self.time = datetime.datetime.now()


class BottleDataUploader:
    def __init__(self, engine, bottles):
        super().__init__()
        self.engine = engine
        self.db = self.engine.db
        self.bottles = bottles

    def upload(self) -> None:
        for bottle in self.bottles:
            self.db.collection("bottles").document(bottle.id).set({
                u'history': firestore.firestore.ArrayUnion([{
                    u'percent_left': bottle.percent_left,
                    u'time': datetime.datetime.utcnow()
                }])
            }, merge=True)


class WaterLevelDetectionThread(threading.Thread):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.cv2 = self.engine.cv2
        self.pwmled = engine.pwmled

        # init camera
        self.cap = self.cv2.VideoCapture(0)
        self.cap.set(self.cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(self.cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(self.cv2.CAP_PROP_BUFFERSIZE, 1)

        self.img_save_path = "/home/pi/Desktop/project/app/captures"

    def rotate_image(self, image, image_center, angle):
        rot_mat = self.cv2.getRotationMatrix2D(image_center, angle, 1.0)
        result = self.cv2.warpAffine(
            image, rot_mat, image.shape[1::-1], flags=self.cv2.INTER_LINEAR)
        return result

    def _should_stop(self):
        return self.engine.should_stop_scanning

    def run(self) -> None:
        print("Scanning on progress...")
        height = [0 for i in range(5)]

        os.chdir(self.img_save_path)

        if self._should_stop():
            print("[!] Scanned canceled by engine.")
            return
        imgs = []
        # take pictures
        for i in range(5):
            print(i)
            self.pwmled[i*2].on()
            time.sleep(0.05)
            if(i == 0):
                ret, frame = self.cap.read()
            ret, frame = self.cap.read()

            # self.cv2.imwrite(str(i)+'.jpg', frame)
            imgs.append(frame)

            self.pwmled[i*2].off()
            time.sleep(0.05)

        if self._should_stop():
            print("[!] Scanned canceled by engine.")
            return

        print("Recognizing in progress...")

        # ai
        # imgs = [
        #     self.cv2.imread('0.jpg', self.cv2.IMREAD_UNCHANGED),
        #     self.cv2.imread('1.jpg', self.cv2.IMREAD_UNCHANGED),
        #     self.cv2.imread('2.jpg', self.cv2.IMREAD_UNCHANGED),
        #     self.cv2.imread('3.jpg', self.cv2.IMREAD_UNCHANGED),
        #     self.cv2.imread('4.jpg', self.cv2.IMREAD_UNCHANGED),
        # ]

        rotate_degs = [6, 0, -2, -5, -9]

        regions = [
            (59, 0, 296, 604),
            (399, 82, 657, 593),
            (673, 135, 918, 575),
            (893, 177, 1121, 555),
            (1080, 200, 1279, 531)
        ]
        result_roi_mats = []
        for idx, img in enumerate(imgs):

            x1, y1, x2, y2 = regions[idx]
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            if rotate_degs[idx] != 0:
                img = self.rotate_image(img, (cx, cy), rotate_degs[idx])
            roi = img[y1:y2, x1:x2]
            mask = roi > np.array([150, 100, 100])
            mask = mask[:, :, 0] & mask[:, :, 1] & mask[:, :, 2]
            print(mask.shape)
            h, w = mask.shape
            result_roi = roi.copy()

            last_triggered = False
            thresh = 65

            for i in range(h-1-40, -1, -1):
                sum = np.sum(mask[i, :])
                if sum > thresh:
                    if not last_triggered:
                        last_triggered = True
                else:
                    if last_triggered:
                        result_roi[i+1, :, :] = 255
                        height[idx] = (h-i+1)/h
                        break

            print(height[idx])

            if self._should_stop():
                print("[!] Scanned canceled by engine.")
                return

            result_roi_mats.append(result_roi)

        bottles = []
        print(height)
        for i in range(5):
            bottles.append(Bottle(str(i), height[i]))
        print("Uploading in progress...")

        if self._should_stop():
            print("[!] Scanned canceled by engine.")
            return

        uploader = BottleDataUploader(self.engine, bottles)
        uploader.upload()

        print("Upload done!")

        # write to disk
        print("Writing images to disk...")
        for i, img in enumerate(imgs):
            self.cv2.imwrite(str(i)+'.jpg', img)
        print("Writing results to disk...")
        for i, img in enumerate(result_roi_mats):
            self.cv2.imwrite(f"{i}_result.jpg", img)
        print("Done")

#print("Im' working")

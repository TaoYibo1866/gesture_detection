from threading import Thread, Lock
import sys
if "/opt/ros/lunar/lib/python2.7/dist-packages" in sys.path:
    sys.path.remove("/opt/ros/lunar/lib/python2.7/dist-packages")
import cv2

class WebcamVideoStream :
    def __init__(self, src = 0, width = 640, height = 480):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        (self.grabbed, self.frame) = self.stream.read()
        self.started = False
        self.flag = None
        self.temp = self.flag
        self.read_lock = Lock()

    def start(self) :
        if self.started :
            print ("already started!!")
            return None
        self.started = True
        self.thread = Thread(target=self.update, args=())
        self.thread.start()
        return self

    def update(self) :
        while self.started :
            if self.flag != self.temp:
                self.temp = self.flag
                if self.flag :
                    self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
                    self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
                else:
                    self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            (grabbed, frame) = self.stream.read()
            self.read_lock.acquire()
            self.grabbed, self.frame = grabbed, frame
            self.read_lock.release()

    def read(self) :
        self.read_lock.acquire()
        frame = self.frame.copy()
        self.read_lock.release()
        return frame

    def stop(self) :
        self.started = False
        self.thread.join()

    def bigger(self):
        self.flag = False

    def smaller(self):
        self.flag = True

    def __exit__(self, exc_type, exc_value, traceback) :
        self.stream.release()

if __name__ == "__main__" :
    vs = WebcamVideoStream().start()
    while True :
        frame = vs.read()
        cv2.imshow('webcam', frame)
        if cv2.waitKey(1) == 27 :
            break

    vs.stop()
    cv2.destroyAllWindows()

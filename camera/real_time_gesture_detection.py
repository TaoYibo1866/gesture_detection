import argparse
import os
import sys
if "/opt/ros/lunar/lib/python2.7/dist-packages" in sys.path:
    sys.path.remove("/opt/ros/lunar/lib/python2.7/dist-packages")
from load_model import detector
from gesture_action import select_highest_score
from gesture_action import serial_init
from camera_thread import WebcamVideoStream
import cv2
import numpy as np
import time


def parse_arguments(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-model', help='the name of model', default="FRCNN")
    parser.add_argument('-camera', help='webcamera:0 camera:1', type=int, default=0)
    parser.add_argument('-threshold', help='score threshore', type=float, default=0.5)
    parser.add_argument("-servo", action="store_true", default=False)
    return parser.parse_args(argv)


def main(argv):
    model_name = argv.model
    camera = argv.camera
    threshold = argv.threshold
    servo = argv.servo
    if servo:
        ser = serial_init()
    else:
        ser = None
    script_path = os.path.abspath(__file__)
    detector_path = os.path.abspath(os.path.join(script_path, '..', model_name, 'frozen_inference_graph.pb'))
    gesture_detector = detector(detector_path)
    print("////////\n{}\n////////".format(argv))
    camera_thread = WebcamVideoStream(src=camera).start()
    frame_interval = 3
    frame_count = 0
    start_time = time.time()
    while True:
        frame = camera_thread.read()
        frame_count += 1
        if (frame_count % frame_interval) == 0:
            frame_count = 0
            (boxes, scores, classes, num) = gesture_detector.run(frame)
            end_time = time.time()
            fps = int(frame_interval/(end_time-start_time))
            start_time = end_time
            select_highest_score(
                frame,
                np.squeeze(boxes),
                np.squeeze(classes).astype(np.int32),
                np.squeeze(scores),
                camera_thread,
                serial = ser,
                min_score_thresh=threshold)
            cv2.putText(frame, str(fps) + " fps", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0),
                        thickness=2, lineType=2)
            cv2.imshow('result', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    cv2.destroyAllWindows()
    camera_thread.stop()


if __name__ == "__main__":
    main(parse_arguments(sys.argv[1:]))

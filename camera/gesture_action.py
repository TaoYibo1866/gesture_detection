import numpy as np
import sys
if "/opt/ros/lunar/lib/python2.7/dist-packages" in sys.path:
    sys.path.remove("/opt/ros/lunar/lib/python2.7/dist-packages")
import cv2
import datetime
import os
import serial

screen_shot_path = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
ok = False
ok_count = 0
img_count = 1

flag = False
flag_count = 0
mode = 0


def select_highest_score(
    image,
    boxes,
    classes,
    scores,
    camera_thread,
    serial=None,
    min_score_thresh=0.5):

    font = cv2.FONT_HERSHEY_COMPLEX
    im_height, im_width, dim = image.shape
    s = np.max(scores)
    if scores is not None and s > min_score_thresh:
        index = np.argwhere(scores == s).reshape(1, -1).tolist()[0]
        for i in index:
            ymin, xmin, ymax, xmax = boxes[i].tolist()
            xmin = int(xmin*im_width)
            xmax = int(xmax*im_width)
            ymin = int(ymin*im_height)
            ymax = int(ymax*im_height)
            c = classes[i]
            if c == 1:
                name = 'one'
                color = (0, 255, 0)
                #cv2.putText(image, 'slide to change window size', (10, 10), font, 0.5, (255, 0, 0), 1)
                slide_action(image, xmin, xmax, camera_thread)
            elif c == 2:
                name = 'ok'
                color = (0, 255, 0)
                #cv2.putText(image, 'holding this gesture enables screen shot', (10, 10), font, 0.5, (255, 0, 0), 1)
                screen_shot(camera_thread)
            else:
                name = 'five'
                color = (0, 0, 255)
                #cv2.putText(image, 'object tracking mode', (10, 10), font, 0.5, (255, 0, 0), 1)
                if serial is not None:
                   center = (int((xmin+xmax)/2), int((ymin+ymax)/2))
                   if center[0] > im_width / 2 + 0.05 * im_width:
                       serial.write([0x32, 0x0d])
                   elif center[0] < im_width / 2 - 0.05 * im_width:
                       serial.write([0x31, 0x0d])
                   if center[1] > im_height / 2 + 0.05 * im_height:
                       serial.write([0x33, 0x0d])
                   elif center[1] < im_height / 2 - 0.05 * im_height:
                       serial.write([0x34, 0x0d])
            score = str(round(s*100, 2))
            cv2.rectangle(image, (xmin, ymin), (xmax, ymax), color, thickness=3)
            text = name + ':' + score + "%"
            cv2.putText(image, text, (xmin, ymin), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 0, 0), 1)

    return image


def serial_init():
    ser=serial.Serial()
    ser.baudrate = 115200
    ser.port = '/dev/ttyUSB0'
    ser.timeout = 3
    ser.open()
    if ser.isOpen():
        return ser
    else:
        print("////////\ncould not open port\n////////")
        exit()


def tracking_serial(p1, p2, height, width, serial):
    center = (int((p1[0]+p2[0])/2), int((p1[1]+p2[1])/2))
    if center[0] > width / 2 + 0.05 * width:
        serial.write([0x32, 0x0d])
    elif center[0] < width / 2 - 0.05 * width:
        serial.write([0x31, 0x0d])
    if center[1] > height / 2 + 0.05 * height:
        serial.write([0x33, 0x0d])
    elif center[1] < height / 2 - 0.05 * height:
        serial.write([0x34, 0x0d])


def screen_shot(thread):
    global ok
    global ok_count
    global img_count
    global start
    if not ok:
        ok = True
        start = datetime.datetime.now()
        return
    else:
        now = datetime.datetime.now()
        duration = int((now - start).total_seconds()*1000)
        start = now
        if duration < 800:
            ok_count = ok_count + duration
            if ok_count > 3000:
                start = datetime.datetime.now()
                font = cv2.FONT_HERSHEY_PLAIN
                while True:
                    frame = thread.read()
                    now = datetime.datetime.now()
                    duration = int(1000*(now - start).total_seconds())
                    if duration < 1000:
                        cv2.putText(frame, '5', (50, 70), font, 6, (255, 0, 0), 2)
                    elif duration < 2000:
                        cv2.putText(frame, '4', (50, 70), font, 6, (255, 0, 0), 2)
                    elif duration < 3000:
                        cv2.putText(frame, '3', (50, 70), font, 6, (255, 0, 0), 2)
                    elif duration < 4000:
                        cv2.putText(frame, '2', (50, 70), font, 6, (255, 0, 0), 2)
                    elif duration < 5000:
                        cv2.putText(frame, '1', (50, 70), font, 6, (255, 0, 0), 2)
                    elif duration < 5500:
                        cv2.putText(frame, None, (50, 70), font, 6, (255, 0, 0), 2)
                    else:
                        print("////////\n{}\n////////".format(os.path.join(screen_shot_path, str(img_count) + '.png')))
                        cv2.imwrite(os.path.join(screen_shot_path, str(img_count) + '.png'), frame)
                        img_count += 1
                        break
                    cv2.imshow('result', frame)
                    cv2.waitKey(1)
                ok_count = 0
                ok = False
                return
            else:
                return
        else:
            ok_count = 0
            ok = False
            return


def slide_action(image, xmin, xmax, thread):
    global flag
    global begin
    global flag_count
    global x_mid
    global mode

    font = cv2.FONT_HERSHEY_DUPLEX

    if not flag:
        flag = True
        begin = datetime.datetime.now()
        x_mid = (xmin + xmax)/2
        return
    else:
        now = datetime.datetime.now()
        duration = int((now - begin).total_seconds() * 1000)
        begin = now
        if duration < 1000:
            flag_count += 1
        else:
            flag = False
            flag_count = 0
            mode = 0
            return
        if flag_count == 1:
            if (xmin + xmax)/2 > x_mid:
                mode = 1
            elif (xmin + xmax)/2 < x_mid:
                mode = -1
            x_mid = (xmin + xmax)/2
            return
        elif 1< flag_count < 4:
            if mode*((xmin + xmax)/2 - x_mid) < 0:
                flag = False
                flag_count = 0
                mode = 0
                return
            x_mid = (xmin + xmax) / 2
        elif flag_count == 4 and mode*((xmin + xmax)/2 - x_mid) > 0:
            if mode == 1:
                thread.bigger()
                #cv2.putText(image, 'bigger', (50, 50), font, 0.5, (255, 0, 0), 1)
            elif mode == -1:
                thread.smaller()
                #cv2.putText(image, 'smaller', (50, 50), font, 0.5, (255, 0, 0), 1)
            flag = False
            flag_count = 0
            mode = 0
            return
        else:
            flag = False
            flag_count = 0
            mode = 0
            return

import cv2
import asyncio
import serial
import logging

import yaml
import sys
from yolov8_onnx import Model

cfg = yaml.load(open('cfg.yaml', 'r', encoding='utf-8').read(), Loader=yaml.FullLoader)

async def yoloDetect(_cap, _net):
    while True:
        ret, src_img = _cap.read()
        detections = _net.det(src_img)

        for i in range(len(detections)):
            detection = detections[i]
            id = detection['class_id']
            if id == 0:
                # Draw Person
                _net.draw_bounding_box(src_img,
                                      detection['class_id'],
                                      detection['confidence'],
                                      round(detection['box'][0] * detection['scale']),
                                      round(detection['box'][1] * detection['scale']),
                                      round((detection['box'][0] + detection['box'][2]) * detection['scale']),
                                      round((detection['box'][1] + detection['box'][3]) * detection['scale']))

            if (id == 15 or id == 16):
                _net.draw_bounding_box(src_img,
                                      15, # only cat
                                      detection['confidence'],
                                      round(detection['box'][0] * detection['scale']),
                                      round(detection['box'][1] * detection['scale']),
                                      round((detection['box'][0] + detection['box'][2]) * detection['scale']),
                                      round((detection['box'][1] + detection['box'][3]) * detection['scale']))

        row, col, _ = src_img.shape
        roi_img = src_img[20:row - 20, 0:col]
        cv2.imshow('src', roi_img)
        if cv2.waitKey(1) == 27:
            break

def serialWrite(_ser):
    pass

SER_WRITE_INTERVAL = 30
async def intervalSerial(_ser):
    while True:
        await asyncio.sleep(SER_WRITE_INTERVAL)
        serialWrite(_ser)

async def startUp(_cap, _model_path, _inp_size):
    try:
        ser = serial.Serial(port=cfg['serial_port'], baudrate=115200, timeout=0.5)
        cap = cv2.VideoCapture(_cap)
        net = Model(_model_path, _size=_inp_size)
        task_yolo = asyncio.create_task(yoloDetect(_cap= cap, _net= net))
        task_serial = asyncio.create_task(intervalSerial(_ser= ser))
        await asyncio.wait({task_yolo, task_serial})
    except:
        logging.warning("Failed to open the serial port, cancel sending")
        cap = cv2.VideoCapture(_cap)
        net = Model(_model_path, _size=_inp_size)
        task_yolo = asyncio.create_task(yoloDetect(_cap= cap, _net= net))
        await asyncio.wait({task_yolo})

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(startUp(_cap=cfg['cap'],
                                        _model_path=sys.path[0] + '/models/yolov8s-480x.onnx',
                                        _inp_size = (480,480)))

    except KeyboardInterrupt as exc:
        print('Quit.')
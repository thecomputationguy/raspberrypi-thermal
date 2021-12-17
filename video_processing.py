import cv2
from collections import deque
from multiprocessing.pool import ThreadPool
import time, board, busio
import adafruit_mlx90640
import numpy as np
import cmapy
import json
import os

def apply_transformations(image, required_shape):
    width = required_shape[0]
    height = required_shape[1]
    image = cv2.applyColorMap(image, cmapy.cmap('jet'))
    image = cv2.resize(image, (width, height), interpolation=cv2.INTER_CUBIC)
    
    return image

def temperature_to_image(frame, shape, T_min, T_max):
    image = np.uint8((frame - T_min) * 255 / (T_max-T_min))
    image.shape = (shape[1], shape[0])
    return image

def get_video_sequential(device, original_shape, required_shape):
    frame = np.zeros((original_shape[0] * original_shape[1], ))
    print("Runnig Sequential Version")

    while True:
        time_start = time.time()
        device.getFrame(frame)
        t_start = time.time()
        T_min = np.min(frame)
        T_max = np.max(frame)
        image = temperature_to_image(frame, original_shape, T_min, T_max)
        image = apply_transformations(image, required_shape)
        cv2.imshow('Thermal Image', image)
        time_end = time.time()
        print("FPS : ", 1 / (time_end-time_start))

        if cv2.waitKey(1) == ord('q'):
            break   

    cv2.destroyAllWindows()

def get_video_multithreaded(device, original_shape, required_shape):
    frame = np.zeros((original_shape[0] * original_shape[1], ))
    thread_num = cv2.getNumberOfCPUs()
    print("Runnig Paralle Version ; Total CPUs : ", thread_num)
    pool = ThreadPool(processes=thread_num)
    pending_task = deque()

    while True:
        time_start = time.time()
        while len(pending_task) > 0 and pending_task[0].ready():
            res = pending_task.popleft().get()
            cv2.imshow('Thermal Image', res)

        if len(pending_task) < thread_num:
            device.getFrame(frame)
            t_start = time.time()
            T_min = np.min(frame)
            T_max = np.max(frame)
            image = temperature_to_image(frame, original_shape, T_min, T_max)
            task = pool.apply_async(apply_transformations, (image.copy(), required_shape))
            pending_task.append(task)
        
        time_end = time.time()
        print("FPS : ", 1 / (time_end-time_start))
        
        if cv2.waitKey(1) == ord('q'):
            break   

    cv2.destroyAllWindows()

if __name__ == '__main__':
    if (os.path.exists("config.json")):
        print("Reading Config File")
        with open("config.json", 'r') as jsonfile:
            config = json.load(jsonfile)
        print(config)
    else:
        raise FileNotFoundError
    
    frequency = config['frequency']
    scale = config['scale']
    refresh_rate = config['refresh_rate']
    version = config['version']
    
    print('Starting Program')
    i2c = busio.I2C(board.SCL, board.SDA, frequency=frequency)
    mlx = adafruit_mlx90640.MLX90640(i2c)
    mlx.refresh_rate = eval(config['refresh_rate'])
    mlx_shape = (config['mlx_width'], config['mlx_height'])
    mlx_interp_shape = (mlx_shape[0] * scale, mlx_shape[1] * scale)
    
    if version == 'parallel':
        get_video_multithreaded(mlx, mlx_shape, mlx_interp_shape)
    else:
        get_video_sequential(mlx, mlx_shape, mlx_interp_shape)

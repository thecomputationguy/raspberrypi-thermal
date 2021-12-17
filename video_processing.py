import cv2
from collections import deque
from multiprocessing.pool import ThreadPool
import time, board, busio
import adafruit_mlx90640
import numpy as np
import cmapy

def apply_transformations(image, required_shape):
    width = required_shape[0]
    height = required_shape[1]
    image = cv2.applyColorMap(image, cmapy.cmap('jet'))
    image = cv2.resize(image, (width, height), interpolation=cv2.INTER_CUBIC)
    
    return image

def temperature_to_image(frame, T_min, T_max):
    image = np.uint8((frame - T_min) * 255 / (T_max-T_min))
    image.shape = (24,32)
    return image

def get_video(device, original_shape, required_shape):
    frame = np.zeros((original_shape[0] * original_shape[1], ))
    thread_num = cv2.getNumberOfCPUs()
    print("Total CPUs : ", thread_num)
    pool = ThreadPool(processes=thread_num)
    pending_task = deque()

    while True:
        while len(pending_task) > 0 and pending_task[0].ready():
            res = pending_task.popleft().get()
            cv2.imshow('Thermal Image', res)

        if len(pending_task) < thread_num:
            device.getFrame(frame)
            t_start = time.time()
            T_min = np.min(frame)
            T_max = np.max(frame)
            image = temperature_to_image(frame, T_min, T_max)
            task = pool.apply_async(apply_transformations, (image.copy(), required_shape))
            pending_task.append(task)

        if cv2.waitKey(1) == ord('q'):
            break   

    cv2.destroyAllWindows()

if __name__ == '__main__':
    print('Running Program')
    i2c = busio.I2C(board.SCL, board.SDA, frequency=1000000)
    mlx = adafruit_mlx90640.MLX90640(i2c)
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ
    mlx_shape = (24,32)
    mlx_interp_val = 10
    mlx_interp_shape = (mlx_shape[0] * mlx_interp_val, mlx_shape[1] * mlx_interp_val)    
    get_video(mlx, mlx_shape, mlx_interp_shape)
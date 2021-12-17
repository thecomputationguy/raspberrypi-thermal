import cv2
from collections import deque
from multiprocessing.pool import ThreadPool
import time
import numpy as np
import cmapy

def apply_transformations(frame, required_shape, original_shape, T):
    """
    Method to convert the raw frame into temperature map and apply interpolations

    Args:
        frame ([mlx dataframe]): [Thermal dataframe from the MLX device]
        required_shape ([tuple]): [Final shape]
        original_shape ([tuple]): [Original shape of the MLX image]
        T ([tuple]): [Contains minimum and maximum temperature of the frame]

    Returns:
        [image]: [final transformed image from the raw frame]
    """
    image = temperature_to_image(frame, original_shape, T[0], T[1])
    width = required_shape[0]
    height = required_shape[1]
    image = cv2.applyColorMap(image, cmapy.cmap('jet'))
    image = cv2.resize(image, (width, height), interpolation=cv2.INTER_CUBIC)
    
    return image

def temperature_to_image(frame, shape, T_min, T_max):
    """
    Converts the temperature field of the MLX frame to an image array

    Args:
        frame ([mlx dataframe]): [Thermal dataframe from the MLX device]
        shape ([tuple]): [Final shape]
        T_min ([float]): [Minimum temperature in the frame]
        T_max ([float]): [Maximum temperature in the frame]

    Returns:
        [image]: [Image from the raw temperature frame]
    """
    image = np.uint8((frame - T_min) * 255 / (T_max-T_min))
    image.shape = (shape[1], shape[0])
    
    return image

def save_image(image):
    """
    Saves image

    Args:
        image ([np.array]): [thermal image]
    """
    filename = "thermal_image_" + str(time.time()) + ".jpg"
    print("Saving Image...")
    cv2.imwrite(filename, image)
    print("Image Saved.")

def process_video_sequential(device, original_shape, required_shape):
    """
    Performs the thermal image processing using 1 CPU core

    Args:
        device ([MLX Device]): [MLX Camera identifier]
        original_shape ([tuple]): [Original shape of the MLX image]
        required_shape ([tuple]): [Final shape]
    """
    frame = np.zeros((original_shape[0] * original_shape[1], ))
    latency = staticmethod
    print("Runnig Sequential Version")

    while True:
        time_start = time.time()
        device.getFrame(frame)
        t_start = time.time()
        T_min = np.min(frame)
        T_max = np.max(frame)
        image = apply_transformations(frame, required_shape, original_shape, (T_min, T_max))
        time_end = time.time()
        text = f"T_min : {T_min:.1f}C ; T_max : {T_max:.1f}C ; FPS : {1 / (time_end-time_start):.1f} ; Interpolation : INTER_CUBIC"
        cv2.putText(image, text, (30,18), cv2.FONT_HERSHEY_SIMPLEX, .4, (255,255,255), 1)
        cv2.imshow('Thermal Image', image)

        key = cv2.waitKey(1)
        if key == ord('q'):        
            break
        elif key == ord('s'):
            save_image(image)

    cv2.destroyAllWindows()

def process_video_multithreaded(device, original_shape, required_shape):
    """
    Performs the thermal image processing using multiple CPU cores

    Args:
        device ([MLX Device]): [MLX Camera identifier]
        original_shape ([tuple]): [Original shape of the MLX image]
        required_shape ([tuple]): [Final shape]
    """
    frame = np.zeros((original_shape[0] * original_shape[1], ))
    thread_num = cv2.getNumberOfCPUs()
    print("Runnig Paralle Version ; Total CPUs : ", thread_num)
    pool = ThreadPool(processes=thread_num)
    pending_task = deque()

    while True:
        while len(pending_task) > 0 and pending_task[0].ready():
            res = pending_task.popleft().get()
            text = f"T_min : {T_min:.1f}C ; T_max : {T_max:.1f}C ; FPS : {1 / (time_end-time_start):.1f} ; Interpolation : INTER_CUBIC"
            cv2.putText(res, text, (30,18), cv2.FONT_HERSHEY_SIMPLEX, .4, (255,255,255), 1)
            cv2.imshow('Thermal Image (multithreaded)', res)

        if len(pending_task) < thread_num:
            time_start = time.time()
            device.getFrame(frame)
            T_min = np.min(frame)
            T_max = np.max(frame)
            T = (T_min, T_max)
            task = pool.apply_async(apply_transformations,
                                    (frame.copy(), required_shape, original_shape, T))
            pending_task.append(task)
            time_end = time.time()
        
        key = cv2.waitKey(1)
        if key == ord('q'):        
            break
        elif key == ord('s'):
            save_image(res)

    cv2.destroyAllWindows()
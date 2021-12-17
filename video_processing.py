import board, busio
import adafruit_mlx90640
import json
import os
import helper_functions as hp

if __name__ == '__main__':
    if (os.path.exists("config.json")):
        print("Reading Config File")
        with open("config.json", 'r') as jsonfile:
            config = json.load(jsonfile)
    else:
        raise FileNotFoundError
    
    frequency = config['frequency']
    scale = config['scale']
    refresh_rate = config['refresh_rate']
    parallel = config['parallel']
    
    print('Starting Program. At any point, press the S key to save an image or Q to exit.')
    i2c = busio.I2C(board.SCL, board.SDA, frequency=frequency)
    mlx = adafruit_mlx90640.MLX90640(i2c)
    mlx.refresh_rate = eval(config['refresh_rate'])
    mlx_shape = (config['mlx_width'], config['mlx_height'])
    mlx_interp_shape = (mlx_shape[0] * scale, mlx_shape[1] * scale)
    
    if parallel == True:
        hp.process_video_multithreaded(mlx, mlx_shape, mlx_interp_shape)
    else:
        hp.process_video_sequential(mlx, mlx_shape, mlx_interp_shape)

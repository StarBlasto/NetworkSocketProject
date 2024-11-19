# [ANALYSIS]
# Importted modules
import time

# Global variables
last_start_time = 0

# Name: start_track
# Param: None
# Return: None
# Desc: Starts the tracking process before starting a file download
def start_track():
    global last_start_time
    last_start_time = time.time()

# Name: end_track
# Param1: file_size - The size of the file uploaded/downloaded
# Return: (float) - The upload/download speed 
# Desc: Returns the speed at which the file was uploaded or downloaded
def end_track(file_size):
    # Only continues if the file size exists
    if file_size == None:
        return 0
    
    # Rest of the calculations
    global last_start_time
    difference_time = time.time() - last_start_time
    upload_speed = (file_size / difference_time) / (1024 * 1024)

    # Returns the final speed
    return round(upload_speed, 3)
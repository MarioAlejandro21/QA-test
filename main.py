from tkinter import *
from tkinter import ttk

from open_gopro import WirelessGoPro, Params
import threading

from settings_checks import get_human_readable_fw_version
from dotenv import load_dotenv
import os
import serial
import time


load_dotenv()

# /dev/ttyACM0
# C3464250420765





root = Tk()
root.title('GO PRO AUTOTEST')

mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# RESULT LABEL
logger_value = StringVar(value='')
result_label = ttk.Label(mainframe, textvariable=logger_value)

# SN INPUT FIELD
sn_value = StringVar()
sn_input = ttk.Entry(mainframe, width=20, textvariable=sn_value)

# PROGRESS BAR
pb = ttk.Progressbar(mainframe, orient=HORIZONTAL, length=120, mode='indeterminate')

# PAIR BUTTON
pair_button = ttk.Button(mainframe, text="PAIR CAMERA")



def make_image_paths():
    images_path = 'images'

    if not os.path.exists(images_path):
        os.makedirs(images_path)

    stock_path = 'stock_images'

    if not os.path.exists(stock_path):
        os.makedirs(stock_path)

def log_and_reset(msg: str):
        logger_value.set(msg)
        start_test_button['state'] = 'normal'
        pb.stop()


# START TEST BUTTON

from validators import get_model_with_sn_or_none

def test():
    
    pb.start()
    
    start_test_button['state'] = 'disabled'
    logger_value.set('Pairing...')

    sn = sn_value.get()

    model = get_model_with_sn_or_none(sn)
    
    if model == None:
        log_and_reset('Invalid sn or unsupported model')
        return

    last_four_digits = sn[-4:]

    with WirelessGoPro(target= f"GoPro {last_four_digits}", sudo_password=os.environ['PASSWORD']) as gopro:
        
            logger_value.set("Checking settings..")
            
            fw_version = get_human_readable_fw_version(gopro)

            logger_value.set(f"{model}, fw: {fw_version}")
            
            if not gopro.ble_status.band_5ghz_avail.get_value().flatten:
                log_and_reset('5G is not available')
                return

            if not gopro.ble_status.sd_status.get_value().flatten == Params.SDStatus.OK:
                log_and_reset('Failed SD card')
                return
            
            if gopro.ble_status.int_batt_per.get_value().flatten == 0:
                log_and_reset('Failed battery test')
                return
            
            assert gopro.http_command.load_preset_group(group=Params.PresetGroup.PHOTO).is_ok


            make_image_paths()
            
            
            with serial.Serial('/dev/ttyACM0', 9600, timeout= 1) as ser:

                time.sleep(2)

                for letter in ['R','G','B']:

                    media_set_before = set(x["n"] for x in gopro.http_command.get_media_list().flatten)

                    ser.write(letter.encode())

                    time.sleep(0.5)

                    assert gopro.http_command.set_shutter(shutter=Params.Toggle.ENABLE).is_ok

                    time.sleep(0.5)

                    ser.write('X'.encode())
                    
                    media_set_after = set(x["n"] for x in gopro.http_command.get_media_list().flatten)
                
                    last_photo_filename = media_set_after.difference(media_set_before).pop()

                    gopro.http_command.download_file(camera_file = last_photo_filename, local_file= f"images/{letter}.jpg" )
            
            
            logger_value.set("Prepare to take video")
            time.sleep(4)
            for count in [3, 2, 1]:
                logger_value.set(f"{count}")
                time.sleep(1)

            assert gopro.http_command.load_preset_group(group=Params.PresetGroup.VIDEO).is_ok

            media_set_before = set(x["n"] for x in gopro.http_command.get_media_list().flatten)

            logger_value.set("Recording 10 sec video")

            assert gopro.http_command.set_shutter(shutter=Params.Toggle.ENABLE).is_ok

            time.sleep(10)

            assert gopro.http_command.set_shutter(shutter=Params.Toggle.DISABLE).is_ok

            media_set_after = set(x["n"] for x in gopro.http_command.get_media_list().flatten)

            last_photo_filename = media_set_after.difference(media_set_before).pop()

            logger_value.set("Downloading video..")

            gopro.http_command.download_file(camera_file = last_photo_filename, local_file= f"images/video.mp4" )


    

    start_test_button['state'] = 'normal'
    logger_value.set(f'Videos and photos ready!')
    time.sleep(2)
    logger_value.set(f'{model} OK, FW: {fw_version}')

    pb.stop()


def threaded_test():
    T = threading.Thread(target=test)
    T.start()


start_test_button = ttk.Button(mainframe, text="START TEST", command=threaded_test)

# CALIBRATION BUTTON

# def capture_stock():
    
#     pb.start()
    
#     make_image_paths()

#     sn = sn_value.get()

#     model = get_model_with_sn_or_none(sn)
    
#     if model == None:
#         log_and_reset('Invalid sn or unsupported model')
#         return

#     last_four_digits = sn[-4:]

#     with WirelessGoPro(target= f"GoPro {last_four_digits}", sudo_password=os.environ['PASSWORD']) as gopro:

#         with serial.Serial('/dev/ttyACM0', 9600, timeout= 1) as ser:

#                 time.sleep(2)

#                 for letter in ['R','G','B']:

#                     media_set_before = set(x["n"] for x in gopro.http_command.get_media_list().flatten)

#                     ser.write(letter.encode())

#                     time.sleep(0.5)

#                     assert gopro.http_command.set_shutter(shutter=Params.Toggle.ENABLE).is_ok

#                     time.sleep(0.5)

#                     ser.write('X'.encode())
                    
#                     media_set_after = set(x["n"] for x in gopro.http_command.get_media_list().flatten)
                
#                     last_photo_filename = media_set_after.difference(media_set_before).pop()

#                     gopro.http_command.download_file(camera_file = last_photo_filename, local_file= f"stock_images/{letter}_stock.jpg" )

#                     pb.stop()

#                     log_and_reset("Calibration complete!")

# def threaded_calibration():
#     T = threading.Thread(target=capture_stock)
#     T.start()

# calibration_button = ttk.Button(mainframe, text="CALIBRATE", command=threaded_calibration)

# RENDER ELEMENTS IN WINDOW
sn_input.grid(column=0, row=0)
#calibration_button.grid(column=0, row=1)
start_test_button.grid(column=0, row=2)
pb.grid(column=0, row=3)
result_label.grid(column=0, row=4)

sn_input.focus()



root.mainloop()

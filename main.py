from tkinter import *
from tkinter import ttk

from open_gopro import WirelessGoPro, Params
import threading

from settings_checks import get_human_readable_fw_version
import os
import serial
import time
from audio import play_wav_file
import cv2
from video_player import play_video
from dotenv import load_dotenv
load_dotenv()


SERIAL_PORT = os.getenv('SERIAL_PORT')
COMMAND_FILE_NAME = "gopro_take_a_photo.wav"
MEDIA_FOLDER = os.getenv('MEDIA_FOLDER')

root = Tk()
root.title("GO PRO AUTOTEST")

mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# RESULT LABEL
logger_value = StringVar(value="")
result_label = ttk.Label(mainframe, textvariable=logger_value)

# SN INPUT FIELD
sn_value = StringVar(value="C3464250420765")
sn_input = ttk.Entry(mainframe, width=20, textvariable=sn_value)

# PROGRESS BAR
pb = ttk.Progressbar(mainframe, orient=HORIZONTAL, length=120, mode="indeterminate")

# PAIR BUTTON
pair_button = ttk.Button(mainframe, text="PAIR CAMERA")


def log_and_close_connection(msg: str, gopro: WirelessGoPro):
    logger_value.set(msg)
    start_test_button["state"] = "normal"
    gopro.close()
    pb.stop()


def threaded_fun(fun):
    T = threading.Thread(target=fun)
    T.start()


def take_and_download_image(
    gopro: WirelessGoPro, serial_driver, char_name: str, dest: str
):
    media_set_before = set(x["n"] for x in gopro.http_command.get_media_list().flatten)

    serial_driver.write(char_name.encode())

    assert gopro.http_command.set_shutter(shutter=Params.Toggle.ENABLE).is_ok
    
    time.sleep(0.5)

    serial_driver.write("X".encode())

    time.sleep(2)

    media_set_after = set(x["n"] for x in gopro.http_command.get_media_list().flatten)

    last_photo_filename = media_set_after.difference(media_set_before).pop()

    if not os.path.exists(dest):
        os.makedirs(dest)

    gopro.http_command.download_file(
        camera_file=last_photo_filename, local_file=f"{dest}/{char_name}.jpg"
    )


# START TEST BUTTON

from validators import get_model_with_sn_or_none


def test():
    pb.start()

    start_test_button["state"] = "disabled"
    logger_value.set("Pairing...")

    sn = sn_value.get()

    model = get_model_with_sn_or_none(sn)

    if model == None:
        logger_value.set("Invalid sn or unsupported model")
        return

    last_four_digits = sn[-4:]

    try:
        gopro = WirelessGoPro(target=f"GoPro {last_four_digits}", wifi_interface="Wi-Fi 2")
        gopro.open()
    except:
        logger_value.set("Failed to found wireless device.")
        pb.stop()
        start_test_button["state"] = 'normal'
        return
    
    logger_value.set("Checking settings..")

    fw_version = get_human_readable_fw_version(gopro)

    logger_value.set(f"{model}, fw: {fw_version}")

    if gopro.ble_status.video_rem.get_value().flatten < 1:
        log_and_close_connection("Format SD and try again.", gopro)
        return

    if gopro.ble_status.batt_present.get_value().flatten == False:
        log_and_close_connection("Battery not recognized.", gopro)
        return

    if gopro.ble_status.batt_ok_ota.get_value().flatten == False:
        log_and_close_connection("Not enough battery level to continue", gopro)
        return

    if not gopro.ble_status.band_5ghz_avail.get_value().flatten:
        log_and_close_connection("5G is not available.", gopro)
        return

    if not gopro.ble_status.sd_status.get_value().flatten == Params.SDStatus.OK:
        log_and_close_connection("Failed SD card.", gopro)
        return
    
    if model != "Hero11 Pismo":

        assert gopro.http_command.load_preset_group(
            group=Params.PresetGroup.PHOTO
        ).is_ok

        time.sleep(0.3)

        logger_value.set("Testing voice command")

        media_set_before = set(
            x["n"] for x in gopro.http_command.get_media_list().flatten
        )

        play_wav_file(f"audio/{COMMAND_FILE_NAME}")

        time.sleep(2)

        media_set_after = set(
            x["n"] for x in gopro.http_command.get_media_list().flatten
        )

        if len(media_set_before) == len(media_set_after):
            log_and_close_connection("failed voice command", gopro)
            return
        
        last_photo_filename = media_set_after.difference(media_set_before).pop()

        if not os.path.exists(MEDIA_FOLDER):
            os.makedirs(MEDIA_FOLDER)

        gopro.http_command.download_file(camera_file=last_photo_filename, local_file=f"{MEDIA_FOLDER}/X.jpg")


        logger_value.set("Taking testing images...")

        with serial.Serial(SERIAL_PORT, 9600, timeout=1) as ser:
            time.sleep(2)
            ser.write("X".encode())
            time.sleep(3)

            # TAKE COLOR IMAGES

            for letter in ["W", "R", "G", "B"]:
                take_and_download_image(
                    gopro=gopro, serial_driver=ser, char_name=letter, dest=MEDIA_FOLDER
                )

        for letter in ['W', 'X', 'R', 'G', 'B']:
            img = cv2.imread(f'{MEDIA_FOLDER}/{letter}.jpg', )
            cv2.namedWindow(f"{letter}", cv2.WINDOW_NORMAL)
            cv2.setWindowProperty(winname=f"{letter}", prop_id=cv2.WND_PROP_FULLSCREEN, prop_value=cv2.WINDOW_FULLSCREEN)
            cv2.imshow(winname=f"{letter}", mat=img)
            code = cv2.waitKey(0)
            if code == 120:
                log_and_close_connection("Failed image test", gopro)
                cv2.destroyAllWindows()
                return
            cv2.destroyAllWindows()

    logger_value.set("Prepare to take video")
    time.sleep(4)
    for count in [3, 2, 1]:
        logger_value.set(f"{count}")
        time.sleep(1)

    assert gopro.http_command.load_preset_group(
        group=Params.PresetGroup.VIDEO
    ).is_ok

    media_set_before = set(
        x["n"] for x in gopro.http_command.get_media_list().flatten
    )

    logger_value.set("Recording 10 sec video")

    assert gopro.http_command.set_shutter(shutter=Params.Toggle.ENABLE).is_ok

    time.sleep(10)

    assert gopro.http_command.set_shutter(shutter=Params.Toggle.DISABLE).is_ok

    media_set_after = set(
        x["n"] for x in gopro.http_command.get_media_list().flatten
    )

    last_photo_filename = media_set_after.difference(media_set_before).pop()

    logger_value.set("Downloading video..")

    gopro.http_command.download_file(
        camera_file=last_photo_filename, local_file=f"{MEDIA_FOLDER}/video.mp4"
    )

    gopro.close()

    play_video(f"{MEDIA_FOLDER}/video.mp4")
            

    start_test_button["state"] = "normal"
    logger_value.set(f"Test ended {model}, FW: {fw_version}")

    pb.stop()


start_test_button = ttk.Button(
    mainframe, text="START TEST", command=lambda: threaded_fun(test)
)


# RENDER ELEMENTS IN WINDOW
sn_input.grid(column=0, row=0)
start_test_button.grid(column=0, row=2)
pb.grid(column=0, row=4)
result_label.grid(column=0, row=5)

start_test_button.focus()


root.mainloop()

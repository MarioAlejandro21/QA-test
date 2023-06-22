from tkinter import *
from tkinter import ttk

from open_gopro import WirelessGoPro, Params
import threading

from settings_checks import get_human_readable_fw_version
from dotenv import load_dotenv
import os
import serial
import time
from audio import play_wav_file
from pixel_detection import delta_less_than


load_dotenv()

# /dev/ttyACM0
# C3464250420765

SERIAL_PORT = "COM11"
COMMAND_FILE_NAME = "gopro_take_photo.wav"


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


def make_image_paths():
    images_path = "images"

    if not os.path.exists(images_path):
        os.makedirs(images_path)

    stock_path = "stock_images"

    if not os.path.exists(stock_path):
        os.makedirs(stock_path)


def log_and_reset(msg: str):
    logger_value.set(msg)
    start_test_button["state"] = "normal"
    pb.stop()


def threaded_fun(fun):
    T = threading.Thread(target=fun)
    T.start()


# START TEST BUTTON

from validators import get_model_with_sn_or_none


def test():
    pb.start()

    start_test_button["state"] = "disabled"
    logger_value.set("Pairing...")

    sn = sn_value.get()

    model = get_model_with_sn_or_none(sn)

    if model == None:
        log_and_reset("Invalid sn or unsupported model")
        return

    last_four_digits = sn[-4:]

    with WirelessGoPro(target=f"GoPro {last_four_digits}") as gopro:
        logger_value.set("Checking settings..")

        fw_version = get_human_readable_fw_version(gopro)

        logger_value.set(f"{model}, fw: {fw_version}")

        if gopro.ble_status.video_rem.get_value().flatten < 1:
            log_and_reset("Format SD and try again.")
            return

        if gopro.ble_status.batt_present.get_value().flatten == False:
            log_and_reset("Battery not recognized.")
            return

        if gopro.ble_status.batt_ok_ota.get_value().flatten == False:
            log_and_reset("Not enough battery level to continue")
            return

        if not gopro.ble_status.band_5ghz_avail.get_value().flatten:
            log_and_reset("5G is not available.")
            return

        if not gopro.ble_status.sd_status.get_value().flatten == Params.SDStatus.OK:
            log_and_reset("Failed SD card.")
            return

        assert gopro.http_command.load_preset_group(
            group=Params.PresetGroup.PHOTO
        ).is_ok

        make_image_paths()

        with serial.Serial(SERIAL_PORT, 9600, timeout=1) as ser:
            time.sleep(2)

            for letter in ["R", "G", "B"]:
                media_set_before = set(
                    x["n"] for x in gopro.http_command.get_media_list().flatten
                )

                ser.write(letter.encode())

                time.sleep(0.2)

                assert gopro.http_command.set_shutter(
                    shutter=Params.Toggle.ENABLE
                ).is_ok

                time.sleep(0.5)

                ser.write("X".encode())

                media_set_after = set(
                    x["n"] for x in gopro.http_command.get_media_list().flatten
                )

                last_photo_filename = media_set_after.difference(media_set_before).pop()

                gopro.http_command.download_file(
                    camera_file=last_photo_filename, local_file=f"images/{letter}.jpg"
                )

        media_set_before = set(
            x["n"] for x in gopro.http_command.get_media_list().flatten
        )

        logger_value.set("Comparing pictures...")

        if not (
            delta_less_than("stock_images/R.jpg", "images/R.jpg", 30)
            and delta_less_than("stock_images/B.jpg", "images/B.jpg", 30)
            and delta_less_than("stock_images/G.jpg", "images/G.jpg", 30)
        ):
            log_and_reset("Failed image test")
            return

        logger_value.set("Testing voice command")

        play_wav_file(f"audio/{COMMAND_FILE_NAME}")

        time.sleep(2)

        media_set_after = set(
            x["n"] for x in gopro.http_command.get_media_list().flatten
        )

        if len(media_set_before) == len(media_set_after):
            log_and_reset("failed voice command")
            return

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
            camera_file=last_photo_filename, local_file=f"images/video.mp4"
        )

    start_test_button["state"] = "normal"
    logger_value.set(f"Videos and photos ready!")
    time.sleep(2)
    logger_value.set(f"{model} OK, FW: {fw_version}")

    pb.stop()


start_test_button = ttk.Button(
    mainframe, text="START TEST", command=lambda: threaded_fun(test)
)

# CALIBRATION BUTTON


def image_calibrate():
    pb.start()

    start_test_button["state"] = "disabled"
    logger_value.set("Pairing...")

    sn = sn_value.get()

    model = get_model_with_sn_or_none(sn)

    if model == None:
        log_and_reset("Invalid sn or unsupported model")
        return

    last_four_digits = sn[-4:]

    with WirelessGoPro(target=f"GoPro {last_four_digits}") as gopro:
        logger_value.set("Calibrating..")
        assert gopro.http_command.load_preset_group(
            group=Params.PresetGroup.PHOTO
        ).is_ok

        make_image_paths()

        with serial.Serial(SERIAL_PORT, 9600, timeout=1) as ser:
            time.sleep(2)

            for letter in ["R", "G", "B"]:
                media_set_before = set(
                    x["n"] for x in gopro.http_command.get_media_list().flatten
                )

                ser.write(letter.encode())

                time.sleep(0.2)

                assert gopro.http_command.set_shutter(
                    shutter=Params.Toggle.ENABLE
                ).is_ok

                time.sleep(0.5)

                ser.write("X".encode())

                media_set_after = set(
                    x["n"] for x in gopro.http_command.get_media_list().flatten
                )

                last_photo_filename = media_set_after.difference(media_set_before).pop()

                gopro.http_command.download_file(
                    camera_file=last_photo_filename,
                    local_file=f"stock_images/{letter}.jpg",
                )
    start_test_button["state"] = "normal"
    logger_value.set("Calibration complete")
    pb.stop()


image_calibration_button = ttk.Button(
    mainframe, text="IMG. CALIBRATION", command=lambda: threaded_fun(image_calibrate)
)

# RENDER ELEMENTS IN WINDOW
sn_input.grid(column=0, row=0)
start_test_button.grid(column=0, row=2)
image_calibration_button.grid(column=0, row=3)
pb.grid(column=0, row=4)
result_label.grid(column=0, row=5)

sn_input.focus()


root.mainloop()

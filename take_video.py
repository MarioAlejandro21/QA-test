from open_gopro import WirelessGoPro, Params
import time

def get_media_set_snap(gopro: WirelessGoPro) -> set:
    return set(x["n"] for x in gopro.http_command.get_media_list().flatten)

with WirelessGoPro(target= "GoPro 0765", sudo_password="112233") as gopro:
    gopro.ble_command.load_preset_group(group=Params.PresetGroup.VIDEO)
    assert gopro.ble_setting.fps.set(Params.FPS.FPS_30).is_ok
    assert gopro.ble_setting.resolution.set(Params.Resolution.RES_1080).is_ok

    media_set_before = get_media_set_snap(gopro)

    assert gopro.ble_command.set_shutter(shutter=Params.Toggle.ENABLE).is_ok
    time.sleep(10)
    assert gopro.ble_command.set_shutter(shutter=Params.Toggle.DISABLE).is_ok

    media_set_after = get_media_set_snap(gopro)

    video_name = media_set_after.difference(media_set_before).pop()

    gopro.http_command.download_file(camera_file=video_name, local_file=f"videos/{video_name}")




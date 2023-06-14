from open_gopro import WirelessGoPro, Params
import time



with WirelessGoPro(target= "GoPro 0765", sudo_password="112233") as gopro:
    
    assert gopro.http_command.load_preset_group(group=Params.PresetGroup.PHOTO).is_ok
    
    media_set_before = set(x["n"] for x in gopro.http_command.get_media_list().flatten)

    for i in range(3):
        assert gopro.http_command.set_shutter(shutter=Params.Toggle.ENABLE).is_ok
        time.sleep(1)
    
    media_set_after = set(x["n"] for x in gopro.http_command.get_media_list().flatten)


    last_photos_filenames = media_set_after.difference(media_set_before)

    print("Downloading photos...")
    for filename in last_photos_filenames:
        gopro.http_command.download_file(camera_file = filename, local_file= f"images/{filename}"   )

    print("Photos ready!")

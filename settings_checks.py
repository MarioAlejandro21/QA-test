from open_gopro import WirelessGoPro, Params



def get_model_and_version(gopro):
    res = gopro.ble_command.get_hardware_info()

    actual_version = res["firmware_version"][7:12]
    model = res["model_name"]

    return (model, actual_version)
    



with WirelessGoPro(target= "GoPro 0765", sudo_password="112233") as gopro:
    model, version = get_model_and_version(gopro)

    res = gopro.ble_status.band_5ghz_avail.get_value().flatten

    mic = gopro.ble_status.acc_mic_stat.get_value().flatten

    connected = gopro.ble_status.sd_status.get_value().flatten == Params.SDStatus.OK

    batt_per = gopro.ble_status.int_batt_per.get_value().flatten

    assert gopro.ble_setting.fps.set(Params.FPS.FPS_30).is_ok

    print(batt_per)


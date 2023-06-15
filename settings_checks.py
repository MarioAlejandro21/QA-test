


def get_human_readable_fw_version(gopro):
    res = gopro.ble_command.get_hardware_info()

    actual_version = res["firmware_version"][7:12]

    return actual_version
    


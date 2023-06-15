from re import match

def get_model_with_sn_or_none(sn):
    lookup_model_info = [
        {"sn_pattern": "^C344(?:13|34|42)", "folder_name": "Hero9 Black"},
        {"sn_pattern": "^C346(?:13|42)", "folder_name": "Hero10 Black"},
        {"sn_pattern": "^C349(?:11|42)", "folder_name": "Hero11 Pismo"},
        {"sn_pattern": "^C34713", "folder_name": "Hero11 Sultan"}
    ]
    result = None
    for info in lookup_model_info:
        pattern = info["sn_pattern"]
        folder = info["folder_name"]

        if match(pattern=pattern, string=sn):
            result = folder
            break

    return result
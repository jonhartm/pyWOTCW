import json
import os.path

if not os.path.isfile("settings.json"):
    print("No settings file found... Creating default")
    with open("settings.json", 'w') as settingsFile:
        json.dump({
            "DMG_BREAKS":[1200, 1350, 1400, 1500],
            "SPOT_BREAKS":[2,4,6,8],
            "ATTENDANCE_BREAKS":[.2,.4,.6,.8],
            "HIT_PERCENT_BREAKS":[72.6,75.8,77.7,81]
        }, settingsFile)

with open("settings.json", 'r') as settingsFile:
    settings = json.load(settingsFile)
    DMG_BREAKS = settings["DMG_BREAKS"]
    SPOT_BREAKS = settings["SPOT_BREAKS"]
    ATTENDANCE_BREAKS = settings["ATTENDANCE_BREAKS"]
    HIT_PERCENT_BREAKS = settings["HIT_PERCENT_BREAKS"]

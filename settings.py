import json
import os.path

if not os.path.isfile("settings.json"):
    print("No settings file found... Creating default")
    with open("settings.json", 'w') as settingsFile:
        json.dump({
            "DMG_BREAKS":[1200, 1350, 1400, 1500],
            "SPOT_BREAKS":[3.79,4.1,4.66,5.36],
            "ATTENDANCE_BREAKS":[.2,.4,.6,.8],
            "HIT_PERCENT_BREAKS":[60.3,64.8,69.2,73.2],
            "META_TANK_RANKS":
            {
                5:[],
                4:[],
                3:[],
                2:[],
                1:[]
            }
        }, settingsFile)

with open("settings.json", 'r') as settingsFile:
    settings = json.load(settingsFile)
    DMG_BREAKS = settings["DMG_BREAKS"]
    SPOT_BREAKS = settings["SPOT_BREAKS"]
    ATTENDANCE_BREAKS = settings["ATTENDANCE_BREAKS"]
    HIT_PERCENT_BREAKS = settings["HIT_PERCENT_BREAKS"]

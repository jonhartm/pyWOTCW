import json
import os.path

settings_file = "settings.json"

options = {}

# in case there is no settings file present, make one and throw in some defaults
if not os.path.isfile(settings_file):
    print("No settings file found... Creating default")
    with open(settings_file, 'w') as f:
        json.dump({
        "DMG_BREAKS":[1200, 1350, 1400, 1500],
        "SPOT_BREAKS":[3.79,4.1,4.66,5.36],
        "ATTENDANCE_BREAKS":[.2,.4,.6,.8],
        "HIT_PERCENT_BREAKS":[60.3,64.8,69.2,73.2],
        "WIN_RATE_BREAKS":[40,44,48,52],
        "BATTLE_COUNT_BREAKS":[63,135,262,489],
        "META_TANK_RANKS":
        {
            5:[],
            4:[],
            3:[],
            2:[],
            1:[]
        },
        "PAYOUT_MULTIPLIERS":{
            "Purchase":1,
            "1st Mark":2.5,
            "2nd Mark":5,
            "3rd Mark":10
        },
        "PAYOUT_BY_META":[100,25,10,5,1]
        }, f)

def Set(key, value):
    with open(settings_file, 'w') as f:
        options[key] = value
        json.dump(options, f)

# Make sure to load the settings file into this module
with open(settings_file, 'r') as f:
    options = json.load(f)

from os import getenv
import sqlite3 as sqlite
import json
import database
import settings
from util import *

version = 1.1

def check_for_update():
    current_version = float(getenv("VERSION"))
    print("Current Version:",current_version)
    print("Available Version:",version)
    if query_yes_no("This will update the application to the newest available version. Continue?"):
        if current_version < 1.1:
            print("Updating database to 1.1 ...")
            v_11_update()

def v_11_update():
    # pull the wn8 expected values
    print("Creating wn8_expected and pulling values from modXVM...")
    database.ResetWN8Expected()
    # the MemberStats table doesn't have any history, we can just reform that and fill it
    database.ResetMemberStats()
    with database.GetConnection() as conn:
        cur = conn.cursor()
        print("Adding new columns to StatHistory...")
        cur.execute('ALTER TABLE StatHistory ADD COLUMN winPercent REAL')
        cur.execute('ALTER TABLE StatHistory ADD COLUMN battles INTEGER')
        cur.execute('ALTER TABLE StatHistory ADD COLUMN wn8 INTEGER')
        conn.commit()
    # we've added some new items to the settings file...
    print("Updating Settings File...")
    settings_file = getenv("SETTINGS_FILE")
    with open(settings_file, 'r') as f:
        options = json.load(f)
    options["WN8_BREAKS"] = [755,1315,1965,2525]
    options["PUB_BATTLE_BREAKS"] = [10,25,50,100]
    with open(settings_file, 'w') as f:
        json.dump(options, f)

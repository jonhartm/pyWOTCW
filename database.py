#-------------------------------------------------------------------------------
# INIT_DATABASE.PY
# Functions for Creating/Reseting the SQL database
#-------------------------------------------------------------------------------

from os import path, getenv
import sqlite3 as sqlite
from util import Timer
from caching import *

ROOT = path.dirname(path.realpath(__file__))
conn = sqlite.connect(path.join(ROOT, "wotcw.db"))

def InitializeAll():
    ResetTanks()

# drops the specified table from the database
def DropTable(table_name):
    cur = conn.cursor()
    statment = 'DROP TABLE IF EXISTS "{}"'.format(table_name)
    cur.execute(statment)

# drop and then load the "Tanks" table
def ResetTanks():
    try:
        cur = conn.cursor()
        DropTable("Tanks")
        statement = '''
        CREATE TABLE "Tanks" (
            'tank_id' INTEGER NOT NULL PRIMARY KEY,
            'type' TEXT,
            'name' TEXT
        );
        '''
        cur.execute(statement)

        TankListCache = CacheFile('TankListCache.json')
        url = "https://api.worldoftanks.com/wot/encyclopedia/vehicles/"
        params = {
            "application_id": getenv("WG_APP_ID"),
            "fields": "type, name",
            "tier": "10"
        }
        API_data =  TankListCache.CheckCache_API(url, params)["data"]
        inserts = []
        for tank in API_data:
            inserts.append([
                tank,
                API_data[tank]["type"],
                API_data[tank]["name"]
            ])
        statement = 'INSERT INTO Tanks VALUES (?,?,?)'
        cur.executemany(statement, inserts)
        conn.commit()
    except Exception as e:
        print("ERROR: " + str(e))
        print(type(e))

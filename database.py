#-------------------------------------------------------------------------------
# INIT_DATABASE.PY
# Functions for Creating/Reseting the SQL database
#-------------------------------------------------------------------------------

from os import path, getenv
import sqlite3 as sqlite
from util import Timer
from caching import *

def GetConnection():
    ROOT = path.dirname(path.realpath(__file__))
    return sqlite.connect(path.join(ROOT, "wotcw.db"))

def InitializeAll():
    ResetTanks()
    ResetClanMembers()

# drops the specified table from the database
def DropTable(table_name, cur):
    statment = 'DROP TABLE IF EXISTS "{}"'.format(table_name)
    cur.execute(statment)

# drop and then load the "Tanks" table
def ResetTanks():
    with GetConnection() as conn:
        cur = conn.cursor()
        DropTable("Tanks", cur)
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

def ResetClanMembers():
    with GetConnection() as conn:
        cur = conn.cursor()
        DropTable("Members", cur)
        statement = '''
        CREATE TABLE "Members" (
            'account_id' INTEGER NOT NULL PRIMARY KEY,
            'nickname' TEXT,
            'role' TEXT
        );
        '''
        cur.execute(statement)

        ClanDetailsCache = CacheFile('ClanDetails.json')
        url = "https://api.worldoftanks.com/wgn/clans/info/"
        params = {
            "application_id": getenv("WG_APP_ID"),
            "clan_id": getenv("CLAN_ID"),
            "fields": "members.role, members.account_id, members.account_name",
            "game": "wot"
        }
        API_data =  ClanDetailsCache.CheckCache_API(url, params, max_age=dt.timedelta(hours=23))["data"][getenv("CLAN_ID")]["members"]
        inserts = []
        for member in API_data:
            print(member)
            inserts.append([
                member["account_id"],
                member["account_name"],
                member["role"]
            ])
        statement = 'INSERT INTO Members VALUES (?,?,?)'
        cur.executemany(statement, inserts)
        conn.commit()

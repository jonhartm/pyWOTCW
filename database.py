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

        # jinja doesn't like hypens in keys.
        statement = 'UPDATE Tanks SET type="TD" WHERE type="AT-SPG"'
        cur.execute(statement)
        conn.commit()

def ResetClanMembers():
    with GetConnection() as conn:
        cur = conn.cursor()
        DropTable("Members", cur)
        DropTable("MemberStats", cur)
        statement = '''
        CREATE TABLE "Members" (
            'account_id' INTEGER NOT NULL PRIMARY KEY,
            'nickname' TEXT,
            'role' TEXT
        );
        '''
        cur.execute(statement)

        statement = '''
        CREATE TABLE "MemberStats" (
            'account_id' INTEGER NOT NULL,
            'tank_id' INTEGER NOT NULL,
            'battles' INTEGER,
            'damage_dealt' INTEGER,
            'spotting' INTEGER
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
            GetMemberTankStats(member["account_id"])
            inserts.append([
                member["account_id"],
                member["account_name"],
                member["role"]
            ])
        statement = 'INSERT INTO Members VALUES (?,?,?)'
        cur.executemany(statement, inserts)
        conn.commit()

def GetTierTenTankIDs():
    with GetConnection() as conn:
        cur = conn.cursor()
        query = "SELECT tank_id FROM Tanks"
        cur.execute(query)
        # for row in cur: ids.append(row[0])
        return [str(x[0]) for x in cur]

def GetMemberTankStats(account_id):
    account_id = str(account_id)
    MemberDetailsCache = CacheFile('MemberDetails.json')
    url = "https://api.worldoftanks.com/wot/tanks/stats/"
    params = {
        "application_id": getenv("WG_APP_ID"),
        "account_id": account_id,
        "fields": "tank_id, globalmap.battles, globalmap.damage_dealt, globalmap.spotted",
        "in_garage": "1",
        "tank_id": ','.join(GetTierTenTankIDs())
    }
    API_data = MemberDetailsCache.CheckCache_API(url, params, max_age=dt.timedelta(hours=23), rate_limit=True)["data"][account_id]
    with GetConnection() as conn:
        cur = conn.cursor()
        inserts = []
        for stat in API_data:
            inserts.append([
                account_id,
                stat["tank_id"],
                stat["globalmap"]["battles"],
                stat["globalmap"]["damage_dealt"],
                stat["globalmap"]["spotted"]
            ])
        statement = 'INSERT INTO MemberStats VALUES (?,?,?,?,?)'
        cur.executemany(statement, inserts)
        conn.commit()

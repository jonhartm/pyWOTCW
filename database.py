#-------------------------------------------------------------------------------
# INIT_DATABASE.PY
# Functions for Creating/Reseting the SQL database
#-------------------------------------------------------------------------------

from os import path, getenv
import sqlite3 as sqlite
import csv
from util import *
from caching import *

Cache = CacheFile('cache.json')

def GetConnection():
    ROOT = path.dirname(path.realpath(__file__))
    return sqlite.connect(path.join(ROOT, "wotcw.db"))

def InitializeAll():
    ResetTanks()
    ResetClan()

# drops the specified table from the database
def DropTable(table_name, cur):
    print("Dropping Table " + table_name)
    statment = 'DROP TABLE IF EXISTS "{}"'.format(table_name)
    cur.execute(statment)

# drop and then load the "Tanks" table
def ResetTanks(force_update=False):
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

        url = "https://api.worldoftanks.com/wot/encyclopedia/vehicles/"
        params = {
            "application_id": getenv("WG_APP_ID"),
            "fields": "type, name",
            "tier": "10"
        }
        API_data =  Cache.CheckCache_API(url, params, force_update=force_update)["data"]
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

def ResetClan():
    with GetConnection() as conn:
        cur = conn.cursor()
        DropTable("Members", cur)
        statement = '''
        CREATE TABLE "Members" (
            'account_id' INTEGER NOT NULL PRIMARY KEY,
            'nickname' TEXT
        );
        '''
        print("Creating Table 'Members'")
        cur.execute(statement)

        DropTable("MemberStats", cur)
        statement = '''
        CREATE TABLE "MemberStats" (
            'account_id' INTEGER NOT NULL,
            'tank_id' INTEGER NOT NULL,
            'battles' INTEGER,
            'damage_dealt' INTEGER,
            'spotting' INTEGER,

            CONSTRAINT account
                FOREIGN KEY (account_id)
                REFERENCES Members(account_id)
                ON DELETE CASCADE
        );
        '''
        print("Creating Table 'MemberStats'")
        cur.execute(statement)
    UpdateClanMembers()

# Makes a request to the WOT API for the current members of the clan specified in the .env file
# Compares the retrieved list with the current database. New members are added, missing members
# are removed. Details of each are printed.
def UpdateClanMembers():
    with GetConnection() as conn:
        cur = conn.cursor()

        t = Timer()
        t.Start()
        print("Loading Clan Details from WOT API...")
        url = "https://api.worldoftanks.com/wgn/clans/info/"
        params = {
            "application_id": getenv("WG_APP_ID"),
            "clan_id": getenv("CLAN_ID"),
            "fields": "members.account_id, members.account_name",
            "game": "wot"
        }
        API_data = Cache.CheckCache_API(
            url,
            params,
            max_age=dt.timedelta(hours=23)
        )["data"][getenv("CLAN_ID")]["members"]
        print("Clan details found for {} members...".format(len(API_data)))

        current_members = [x for x in cur.execute("SELECT * FROM Members").fetchall()]

        # run through the member list from the API and put any new members into the database
        inserts = []
        for member in API_data:
            if member["account_id"] not in [x[0] for x in current_members]:
                inserts.append([
                    member["account_id"],
                    member["account_name"]
                ])

        cur.executemany('INSERT INTO Members VALUES (?,?)', inserts)
        conn.commit()
        print("Added {} new members...".format(cur.rowcount))
        for x in inserts: print("+ {} ({})".format(x[1], x[0]))

        # run through the database list and see if there are members who are no longer in the api
        deletes = []
        for member in current_members:
            if member[0] not in [x["account_id"] for x in API_data]:
                deletes.append(member)

        cur.executemany("DELETE FROM Members WHERE account_id = ? AND nickname = ?", deletes)
        conn.commit()
        print("Removed {} members...".format(cur.rowcount))
        for x in deletes: print("- {} ({})".format(x[1], x[0]))

        t.Stop()
        print("Clan details loaded in {}".format(t))

        # Load the stats for all of the members
        # GetMemberTankStats(member_ids)

def GetTierTenTankIDs():
    with GetConnection() as conn:
        cur = conn.cursor()
        query = "SELECT tank_id FROM Tanks"
        cur.execute(query)
        # for row in cur: ids.append(row[0])
        return [str(x[0]) for x in cur]

def GetMemberTankStats(account_ids):
    url = "https://api.worldoftanks.com/wot/tanks/stats/"
    params = {
    "application_id": getenv("WG_APP_ID"),
    "fields": "tank_id, globalmap.battles, globalmap.damage_dealt, globalmap.spotted",
    "in_garage": "1",
    "tank_id": ','.join(GetTierTenTankIDs())
    }
    inserts = []
    for id in account_ids:
        params["account_id"] = str(id)
        print("Loading member details for account id {}".format(id))
        API_data = Cache.CheckCache_API(
            url,
            params,
            max_age=dt.timedelta(hours=23),
            rate_limit=True
        )["data"][str(id)]
        for stat in API_data:
            # don't insert stats for tanks that have never been played in CW
            if stat["globalmap"]["battles"] > 0:
                inserts.append([
                    id,
                    stat["tank_id"],
                    stat["globalmap"]["battles"],
                    stat["globalmap"]["damage_dealt"],
                    stat["globalmap"]["spotted"]
                ])
    print("Found statistics on {} tanks...".format(len(inserts)))

    t = Timer()
    t.Start()
    with GetConnection() as conn:
        cur = conn.cursor()
        query = 'INSERT INTO MemberStats VALUES (?,?,?,?,?)'
        cur.executemany(query, inserts)
        conn.commit()
    t.Stop()
    print("Statistics added to DB in {}.".format(t))

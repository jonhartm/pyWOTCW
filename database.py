#-------------------------------------------------------------------------------
# INIT_DATABASE.PY
# Functions for Creating/Reseting the SQL database
#-------------------------------------------------------------------------------

from os import path, getenv
import sqlite3 as sqlite
import csv
from datetime import datetime, timedelta
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

# drops all data about clan members and re-fills from API calls
# basically a full reset minus the tanks call.
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

        DropTable("StatHistory", cur)
        statement = '''
        CREATE TABLE StatHistory (
        	account_id INTEGER,
        	avgDmg INTEGER,
        	HTDmg INTEGER,
        	MTDmg INTEGER,
        	LTSpots INTEGER,
        	TDDmg INTEGER,
        	SPGDmg INTEGER,
        	updated_at TIME,

        	PRIMARY KEY (account_id, updated_at),
            CONSTRAINT account
                FOREIGN KEY (account_id)
                REFERENCES Members(account_id)
                ON DELETE CASCADE
        );
        '''
        print("Creating Table 'StatHistory'")
        cur.execute(statement)

    UpdateClanMembers()

# Makes a request to the WOT API for the current members of the clan specified in the .env file
# Compares the retrieved list with the current database. New members are added, missing members
# are removed. Details of each are printed.
def UpdateClanMembers():
    with GetConnection() as conn:
        cur = conn.cursor()

        # check to see if the tables even exist before we try filling them
        cur.execute("SELECT COUNT() FROM sqlite_master WHERE type='table' AND name='Members'")
        if [x[0] for x in cur][0] is not 1:
            raise Exception("No Tables found: run command 'main.py -reset' and try again.")

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

        # Load the stats for all of the members pulled in with the API
        UpdateMemberTankStats([x["account_id"] for x in API_data])

def GetTierTenTankIDs():
    with GetConnection() as conn:
        cur = conn.cursor()
        query = "SELECT tank_id FROM Tanks"
        cur.execute(query)
        # for row in cur: ids.append(row[0])
        return [str(x[0]) for x in cur]

def UpdateMemberTankStats(account_ids):
    # load tank stats for every account id passed in
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
        # Clear the table
        cur.execute("DELETE FROM MemberStats")

        cur.executemany("INSERT INTO MemberStats VALUES (?,?,?,?,?)", inserts)
        conn.commit()
    t.Stop()
    print("Statistics added to DB in {}.".format(t))
    AddStatHistory()

def AddStatHistory():
    # Aggregate those stats into the Stat History table via a temporary table
    with GetConnection() as conn:
        cur = conn.cursor()

        # check if we qualify based on the most recent stat history and the interval from the .env file
        statment = '''
        SELECT updated_at FROM StatHistory
        GROUP BY updated_at
        ORDER BY updated_at DESC
        LIMIT 1
        '''
        cur.execute(statment)
        try:
            most_recent_update = datetime.strptime([x[0] for x in cur][0], "%Y-%m-%d")
            current_time = datetime.now() + timedelta(hours=1)
            print("Most Recent Stats: {} ago...".format(current_time - most_recent_update))

            if (current_time - most_recent_update) < timedelta(days=int(getenv("DAYS_BETWEEN_STAT_HISTORY"))):
                print("Last stats update was less than {} days ago.".format(getenv("DAYS_BETWEEN_STAT_HISTORY")))
                return
        except Exception as e:
            print("Unable to locate a stat history update...")

        print("Updating Stats...")

        print("Creating avgStats temporary table...")
        DropTable("avgStats", cur)
        statement = '''
        CREATE TABLE avgStats (
        	account_id INTEGER,
        	type TEXT,
        	avgDmg INTEGER,
        	avgSpot INTEGER
        );
        '''
        cur.execute(statement)

        print("Loading avgStats table...")
        statement = '''
        INSERT INTO avgStats
        	SELECT
        		account_id,
        		type,
        		SUM(damage_dealt)/SUM(battles) AS avgDmg,
        		ROUND(SUM(spotting)*1.0/SUM(battles),1) AS avgSpot
        	FROM MemberStats
        		JOIN Tanks ON Tanks.tank_id = MemberStats.tank_id
        	GROUP BY account_id, type;
            '''
        cur.execute(statement)

        print("Coallating stats into StatHistory...")
        statement = '''
        INSERT INTO StatHistory
        	SELECT
        		Members.account_id,
        		Overall.avgDmg,
        		HTstats.avgDmg AS Htdmg,
        		MTstats.avgDmg AS MTdmg,
        		LTstats.avgSpot AS LTSpots,
        		TDstats.avgDmg AS TDdmg,
        		SPGstats.avgdmg AS SPGdmg,
        		Date() AS updated_at
        	FROM Members
        		LEFT JOIN (
        			SELECT
        				account_id,
        				SUM(damage_dealt)/SUM(battles) AS avgDmg
        			FROM MemberStats
        			GROUP BY account_id
        		) AS Overall ON Members.account_id = Overall.account_id
        		LEFT OUTER JOIN avgStats as HTstats ON
        			Members.account_id = HTstats.account_id
        			and HTstats.type = "heavyTank"
        		LEFT OUTER JOIN avgStats as MTstats ON
        			Members.account_id = MTstats.account_id
        			and MTstats.type = "mediumTank"
        		LEFT OUTER JOIN avgStats as LTstats ON
        			Members.account_id = LTstats.account_id
        			and LTstats.type = "lightTank"
        		LEFT OUTER JOIN avgStats as TDstats ON
        			Members.account_id = TDstats.account_id
        			and TDstats.type = "TD"
        		LEFT OUTER JOIN avgStats as SPGstats ON
        			Members.account_id = SPGstats.account_id
        			and SPGstats.type = "SPG"
        '''
        cur.execute(statement)
        print("Added StatHistory row for {} players".format(cur.rowcount))

        print("Dropping avgStats temporary table...")
        DropTable("avgStats", cur)

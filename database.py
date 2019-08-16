#-------------------------------------------------------------------------------
# INIT_DATABASE.PY
# Functions for Creating/Reseting the SQL database
#-------------------------------------------------------------------------------

from os import path, getenv
import sqlite3 as sqlite
import urllib, csv
from datetime import datetime, timedelta
from util import *
from caching import *
import get_stats
import settings

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
            'tier' INTEGER,
            'type' TEXT,
            'name' TEXT,
            'meta' INTEGER
        );
        '''
        cur.execute(statement)

        url = "https://api.worldoftanks.com/wot/encyclopedia/vehicles/"
        params = {
            "application_id": getenv("WG_APP_ID"),
            "fields": "tier, type, name",
            "tier": "6,8,9,10"
        }
        API_data =  Cache.CheckCache_API(url, params, force_update=force_update)["data"]
        inserts = []
        for tank in API_data:
            meta = 0
            for meta_rank, tanks in settings.options["META_TANK_RANKS"].items():
                # print("Tank_ID: {}".format(tank))
                if tank in tanks:
                    # print("Found {} in {} - meta {}".format(tank, tanks, meta_rank))
                    meta = meta_rank

            inserts.append([
                tank,
                API_data[tank]["tier"],
                API_data[tank]["type"],
                API_data[tank]["name"],
                meta
            ])
        statement = 'INSERT INTO Tanks VALUES (?,?,?,?,?)'
        cur.executemany(statement, inserts)

        # jinja doesn't like hypens in keys.
        statement = 'UPDATE Tanks SET type="TD" WHERE type="AT-SPG"'
        cur.execute(statement)
        conn.commit()

# Update the Tanks table to reflect the current state of the META_TANK_RANKS setting
def UpdateTankMetaRanks():
    with GetConnection() as conn:
        cur = conn.cursor()
        updates = []
        for rank, tanks in settings.options["META_TANK_RANKS"].items():
            for tank_id in tanks:
                updates.append([
                    rank,
                    tank_id
                ])
        statement = 'UPDATE Tanks SET meta=? WHERE tank_id=?'
        cur.executemany(statement, updates)
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

        ResetMemberStats()

        DropTable("StatHistory", cur)
        statement = '''
        CREATE TABLE StatHistory (
        	account_id INTEGER,
        	avgDmg INTEGER,
        	HTDmg INTEGER,
            HTHitPer INTEGER,
        	MTDmg INTEGER,
            MTHitPer INTEGER,
        	LTSpots INTEGER,
        	TDDmg INTEGER,
            TDHitPer INTEGER,
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

        ResetMOEHistory()

    UpdateClanMembers()

def ResetMemberStats():
    with GetConnection() as conn:
        cur = conn.cursor()
        DropTable("MemberStats", cur)
        statement = '''
        CREATE TABLE "MemberStats" (
            'account_id' INTEGER NOT NULL,
            'tank_id' INTEGER NOT NULL,
            'moe' INTEGER,
            'cw_battles' INTEGER,
            'cw_damage_dealt' INTEGER,
            'cw_spotting' INTEGER,
            'cw_hit_percent' INTEGER,
            'cw_wins' INTEGER,
            'cw_avg_damage_assisted_radio' INTEGER,
            'cw_avg_damage_assisted_track' INTEGER,
            'cw_avg_damage_blocked' INTEGER,
            'cw_explosion_hits' INTEGER,
            'cw_explosion_hits_received' INTEGER,
            'cw_no_damage_direct_hits_recieved' INTEGER,
            'cw_piercings_recieved' INTEGER,
            'all_dropped_capture_points' INTEGER,
            'all_frags' INTEGER,
            'all_spotted' INTEGER,
            'all_damage_dealt' INTEGER,
            'all_winrate' INTEGER,
            'all_battles' INTEGER,
            'wn8' INTEGER,

            CONSTRAINT account
                FOREIGN KEY (account_id)
                REFERENCES Members(account_id)
                ON DELETE CASCADE
        );
        '''
        print("Creating Table 'MemberStats'")
        cur.execute(statement)

# Drop and re-create the MOEHistory table
def ResetMOEHistory():
    with GetConnection() as conn:
        cur = conn.cursor()
        DropTable("MOEHistory", cur)
        statement = '''
        CREATE TABLE MOEHistory (
            account_id INTEGER,
            tank_id INTEGER,
            achv_type TEXT,
            old_val INTEGER,
            new_val INTEGER,
            date_reached TIME,
            date_confirmed TIME,
            payout INTEGER,

            PRIMARY KEY (account_id, tank_id, achv_type)

            CONSTRAINT account
                FOREIGN KEY (account_id)
                REFERENCES Members(account_id)
                ON DELETE CASCADE
        )
        '''
        print("Creating Table 'MOEHistory'")
        cur.execute(statement)

def ResetWN8Expected():
    with GetConnection() as conn:
        cur = conn.cursor()
        DropTable("wn8_expected", cur)
        statement = '''
        CREATE TABLE "wn8_expected" (
            'IDNum' INTEGER NOT NULL PRIMARY KEY,
            'expDef' REAL,
            'expFrag' REAL,
            'expSpot' REAL,
            'expDamage' REAL,
            'expWinRate' REAL
        );
        '''
        cur.execute(statement)

        # fetch the current wn8 expected values
        url = "https://static.modxvm.com/wn8-data-exp/json/wn8exp.json"
        response = urllib.request.urlopen(url)
        data = json.loads(response.read())['data']

        inserts = []
        for i in data:
            inserts.append([
                i['IDNum'],
                i['expDef'],
                i['expFrag'],
                i['expSpot'],
                i['expDamage'],
                i['expWinRate']
            ])
        print("Populating Table 'wn8_expected'")
        cur.executemany('INSERT INTO wn8_expected VALUES (?,?,?,?,?,?)', inserts)
        conn.commit()

def MarkMOEPayment(id, payment):
    with GetConnection() as conn:
        cur = conn.cursor()
        query = '''
        UPDATE MOEHistory
        SET date_confirmed = datetime('now'), payout = ?
        WHERE MOEHistory.rowid = ?
        '''
        cur.execute(query, [payment, id])
        conn.commit()

# Makes a request to the WOT API for the current members of the clan specified in the .env file
# Compares the retrieved list with the current database. New members are added, missing members
# are removed. Details of each are printed.
def UpdateClanMembers(skip_marks=False):
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
            url=url,
            params=params,
            limit_param_keys=['clan_id'],
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
        UpdateMemberTankStats([x["account_id"] for x in API_data], skip_marks)

        # Delete any entries in the MOEHistory table for anyone that just joined the clan
        cur.executemany('DELETE FROM MOEHistory WHERE account_id = ?', [[x[0]] for x in inserts])
        conn.commit()

# params: tier - integer between 1 and 10
#         ids - (optional) a list of integers to include in addition to the tier selected
# returns: a list of strings coorresponding to tank ids that meet the parameters
def GetTankIDs(tier, ids=None):
    with GetConnection() as conn:
        cur = conn.cursor()
        if ids is None:
            query = "SELECT tank_id FROM Tanks WHERE tier = ?"
            cur.execute(query, [tier])
        else:
            id_list = ','.join([str(x) for x in ids])
            query = "SELECT tank_id FROM Tanks WHERE tier = ? OR tank_id IN (?)"
            cur.execute(query, [tier, id_list])
        return [str(x[0]) for x in cur]

def UpdateMemberTankStats(account_ids, skip_marks=False):
    # load tank stats for every account id passed in
    stats_url = "https://api.worldoftanks.com/wot/tanks/stats/"
    stats_params = {
    "application_id": getenv("WG_APP_ID"),
    "fields": '''
        tank_id,
        globalmap,
        all.dropped_capture_points,
        all.frags,
        all.spotted,
        all.damage_dealt,
        all.wins,
        all.battles
    ''',
    "in_garage": "1",
    "tank_id": ','.join(GetTankIDs(10, [16161]))
    }

    # load moe achievements for each account id passed in
    moe_url = "https://api.worldoftanks.com/wot/tanks/achievements/"
    moe_params = {
    "application_id": getenv("WG_APP_ID"),
    "fields": "tank_id, achievements",
    "tank_id": ','.join(GetTankIDs(10, [16161]))
    }

    inserts = []
    moe_inserts = []
    print("Loading details for {} accounts...".format(len(account_ids)))
    for id in account_ids:
        stats_params["account_id"] = str(id)
        # print("Loading member details for account id {}".format(id))
        API_stats_data = Cache.CheckCache_API(
            url=stats_url,
            params=stats_params,
            limit_param_keys=['account_id'],
            max_age=dt.timedelta(hours=23),
            rate_limit=True
        )["data"][str(id)]

        # print("Loading member MOE details for account id {}".format(id))
        moe_params["account_id"] = str(id)
        API_moe_data = Cache.CheckCache_API(
            url=moe_url,
            params=moe_params,
            limit_param_keys=['account_id'],
            max_age=dt.timedelta(hours=23),
            rate_limit=True
        )["data"][str(id)]

        player_tanks = get_stats.GetPlayerTanks(id)

        if API_stats_data is None:
            continue

        for stat in API_stats_data:
            # don't insert stats for tanks that have never been played in CW
            try:
                pierce_percent = round((stat["globalmap"]["piercings"]/stat["globalmap"]["hits"])*100, 1)
            except:
                pierce_percent = 0

            try:
                light_rating = round((stat["globalmap"]["survived_battles"]/stat["globalmap"]["battles"])+(stat["globalmap"]["spotted"]/stat["globalmap"]["battles"]), 2)
            except:
                light_rating = 0

            marks = 0
            for x in API_moe_data:
                if x["tank_id"] == stat["tank_id"]:
                    if "marksOnGun" in x["achievements"]:
                        marks = int(x["achievements"]["marksOnGun"])

            # is this a new tank for this player?
            if stat["tank_id"] not in player_tanks.keys():
                print("{}: this is a new tank for player {}...".format(stat["tank_id"], id))
                moe_inserts.append([
                    id,
                    stat["tank_id"],
                    "tank",
                    0,
                    1,
                    dt.datetime.now().strftime("%Y-%m-%d")
                ])
            # if this is not a new tank, has the player earned a new mark?
            elif marks != player_tanks[stat["tank_id"]]:
                print("{}: player {} has earned a new mark...".format(stat["tank_id"], id))
                moe_inserts.append([
                    id,
                    stat["tank_id"],
                    "moe",
                    player_tanks[stat["tank_id"]],
                    marks,
                    dt.datetime.now().strftime("%Y-%m-%d")
                ])

            inserts.append([
                id,
                stat["tank_id"],
                marks,
                stat["globalmap"]["battles"],
                stat["globalmap"]["damage_dealt"],
                light_rating,
                pierce_percent,
                stat["globalmap"]["wins"],
                stat["globalmap"]["avg_damage_assisted_radio"],
                stat["globalmap"]["avg_damage_assisted_track"],
                stat["globalmap"]["avg_damage_blocked"],
                stat["globalmap"]["explosion_hits"],
                stat["globalmap"]["explosion_hits_received"],
                stat["globalmap"]["no_damage_direct_hits_received"],
                stat["globalmap"]["piercings_received"],
                stat["all"]["dropped_capture_points"],
                stat["all"]["frags"],
                stat["all"]["spotted"],
                stat["all"]["damage_dealt"],
                stat["all"]["wins"],
                stat["all"]["battles"]
            ])
    print("Found statistics on {} tanks...".format(len(inserts)))

    t = Timer()
    t.Start()
    with GetConnection() as conn:
        cur = conn.cursor()
        # Clear the table
        cur.execute("DELETE FROM MemberStats")

        cur.executemany("INSERT INTO MemberStats VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL)", inserts)

        # Calculate the WN8 for each player's tank based on the data we just pulled
        # and save it in a temp table
        print("Calculating per Tank WN8...")
        DropTable("wn8_calcs", cur)
        statement = '''
        CREATE TABLE wn8_calcs AS
        	SELECT
        		account_id,
        		tank_id,
        		ROUND(980*rDAMAGEc + 210*rDAMAGEc*rFRAGc + 155*rFRAGc*rSPOTc + 75*rDEFc*rFRAGc + 145*MIN(1.8,rWINc),0) as wn8
        	FROM
        	(
        		SELECT
        			account_id,
        			tank_id,
        			MAX(0,(rWIN-0.71)/(1-0.71)) as rWINc,
        			MAX(0, (rDAMAGE - 0.22) / (1 - 0.22) ) as rDAMAGEc,
        			MAX(0, MIN(MAX(0, (rDAMAGE - 0.22) / (1 - 0.22) ) + 0.2, (rFRAG - 0.12) / (1 - 0.12))) as rFRAGc,
        			MAX(0, MIN(MAX(0, (rDAMAGE - 0.22) / (1 - 0.22) ) + 0.1, (rSPOT - 0.38) / (1 - 0.38))) as rSPOTc,
        			MAX(0, MIN(MAX(0, (rDAMAGE - 0.22) / (1 - 0.22) ) + 0.1, (rDEF - 0.10) / (1 - 0.10))) as rDEFc
        		FROM
        		(
        			SELECT
        				account_id,
        				tank_id,
        				all_avg_damage_dealt/expDamage as rDAMAGE,
        				all_avg_spotted/expSpot as rSPOT,
        				all_avg_frags/expFrag as rFRAG,
        				all_avg_dropped_capture_points/expDef as rDEF,
        				(all_avg_winrate*100)/expWinRate as rWIN
        			FROM (
        					SELECT
        						account_id,
        						tank_id,
        						(all_dropped_capture_points*1.0)/(all_battles*1.0) as all_avg_dropped_capture_points,
        						(all_frags*1.0)/(all_battles*1.0) as all_avg_frags,
        						(all_spotted*1.0)/(all_battles*1.0) as all_avg_spotted,
        						(all_damage_dealt*1.0)/(all_battles*1.0) as all_avg_damage_dealt,
        						(all_winrate*1.0)/(all_battles*1.0) as all_avg_winrate
        					FROM MemberStats
        					) as MemberStats
        			INNER JOIN wn8_expected
        				ON wn8_expected.IDNum = MemberStats.tank_id
        		)
        	)
        '''
        cur.execute(statement)
        statement = '''
        UPDATE MemberStats
            SET wn8 = (
            	SELECT wn8 FROM wn8_calcs
            	WHERE wn8_calcs.account_id = MemberStats.account_id
            		AND wn8_calcs.tank_id = MemberStats.tank_id)
        '''
        cur.execute(statement)
        DropTable("wn8_calcs", cur)

        if not skip_marks:
            cur.executemany("INSERT INTO MOEHistory VALUES (?,?,?,?,?,?,NULL,NULL)", moe_inserts)
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
        	avgDmg REAL,
        	avgSpot REAL,
            avgHitPercent REAL,
			winPercent REAL,
			battles INTEGER
        );
        '''
        cur.execute(statement)

        print("Loading avgStats table...")
        statement = '''
        INSERT INTO avgStats
        	SELECT
            	account_id,
            	type,
            	SUM(cw_damage_dealt)/SUM(cw_battles) AS avgDmg,
            	ROUND(AVG(cw_spotting)*1.0,2) AS avgSpot,
            	ROUND(AVG(cw_hit_percent),1) AS avgHitPercent,
            	ROUND(SUM(cw_wins)*1.0/SUM(cw_battles)*1.0, 2) AS winPercent,
            	SUM(cw_battles) as battles
            FROM (SELECT * FROM MemberStats WHERE cw_battles > 5) AS Stats
            	JOIN Tanks ON Tanks.tank_id = Stats.tank_id
            GROUP BY account_id, type;
            '''
        cur.execute(statement)

        print("Coallating stats into StatHistory...")
        statement = '''
        INSERT INTO StatHistory
        	SELECT
            	Members.account_id,
            	Overall_limited.avgDmg,
            	HTstats.avgDmg AS HTdmg,
            	HTstats.avgHitPercent AS HTHitPer,
            	MTstats.avgDmg AS MTdmg,
            	MTstats.avgHitPercent AS MTHitPer,
            	LTstats.avgSpot AS LTSpots,
            	TDstats.avgDmg AS TDdmg,
            	TDStats.avgHitPercent AS TDHitPer,
            	SPGstats.avgdmg AS SPGdmg,
            	Date() AS updated_at,
            	Overall.winPercent,
            	Overall.battles,
                Overall.wn8
            FROM Members
            	LEFT JOIN (
            		SELECT
            			account_id,
            			SUM(cw_damage_dealt)/SUM(cw_battles) AS avgDmg
            		FROM (SELECT * FROM MemberStats WHERE cw_battles > 5)
            		GROUP BY account_id
            	) AS Overall_limited ON Members.account_id = Overall_limited.account_id
            	LEFT JOIN (
            		SELECT
            			account_id,
            			ROUND(SUM(cw_wins)*1.0/SUM(cw_battles)*1.0, 2) AS winPercent,
            			SUM(cw_battles) as battles,
                        ROUND(AVG(wn8)) as wn8
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

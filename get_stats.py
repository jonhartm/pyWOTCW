import settings
import database
import sqlite3 as sqlite

def GetStats():
    stats = {}
    with database.GetConnection() as conn:
        cur = conn.cursor()
        query = '''
        SELECT
        	Members.account_id,
        	Members.nickname,
        	avgDmg,
        	HTDmg,
        	MTDmg,
        	LTSpots,
        	TDDmg,
        	SPGDmg,
            HTHitPer,
            MTHitPer,
            TDHitPer
        FROM StatHistory
        	JOIN Members ON StatHistory.account_id = Members.account_id
        WHERE updated_at = (
        	SELECT updated_at
        	FROM StatHistory
        	GROUP BY updated_at
        	ORDER By updated_at DESC
        	LIMIT 1
        )
        ORDER BY nickname COLLATE NOCASE
        '''
        for p in [x for x in cur.execute(query)]:
            player = {
                "nickname":p[1]
            }

            if p[2] is not None:
                player['overall'] = {
                    "dmg":p[2],
                    "rank":GetRank(p[2], settings.options["DMG_BREAKS"])
                }

            if p[3] is not None:
                player['HT'] = {
                    "dmg":p[3],
                    "rank":GetRank(p[3], settings.options["DMG_BREAKS"]),
                    "hitPer":p[8],
                    "hitPerRank":GetRank(p[8], settings.options["HIT_PERCENT_BREAKS"])
                }
            if p[4] is not None:
                player['MT'] = {
                    "dmg":p[4],
                    "rank":GetRank(p[4], settings.options["DMG_BREAKS"]),
                    "hitPer":p[9],
                    "hitPerRank":GetRank(p[9], settings.options["HIT_PERCENT_BREAKS"])
                }
            if p[5] is not None:
                player['LT'] = {
                    "spot":p[5],
                    "rank":GetRank(p[5], settings.options["SPOT_BREAKS"])
                }
            if p[6] is not None:
                player['TD'] = {
                    "dmg":p[6],
                    "rank":GetRank(p[6], settings.options["DMG_BREAKS"]),
                    "hitPer":p[10],
                    "hitPerRank":GetRank(p[10], settings.options["HIT_PERCENT_BREAKS"])
                }
            if p[7] is not None:
                player['SPG'] = {
                    "dmg":p[7],
                    "rank":GetRank(p[7], settings.options["DMG_BREAKS"])
                }
            stats[p[0]] = player
    return stats

def GetRank(value, breaks):
    if value is None: return None
    for rank in range(len(breaks)):
        if value < breaks[rank]:
            return rank + 1
    return 5

def GetIndivStats(account_id):
    stats = {
        "by_tank": {
            "heavyTank":[],
            "mediumTank":[],
            "lightTank":[],
            "SPG":[],
            "TD":[]
            },
        "history": []
    }
    with database.GetConnection() as conn:
        cur = conn.cursor()
        query = '''
        SELECT
        	Tanks.name,
        	Tanks.type,
        	battles,
        	ROUND(damage_dealt*1.0/battles, 2) AS avgDmg,
        	spotting AS avgSpotting,
            hit_percent
        FROM MemberStats
        	JOIN Tanks ON MemberStats.tank_id = Tanks.tank_id
        WHERE account_id = ?
        ORDER BY type, battles DESC
        '''
        cur.execute(query, [account_id])
        for tank in [x for x in cur.fetchall()]:
            if tank[1] == "lightTank":
                stats["by_tank"][tank[1]].append({
                    "name":tank[0],
                    "battles":tank[2],
                    "avgSpot":tank[4],
                    "spotRank":GetRank(tank[4], settings.options["SPOT_BREAKS"])
                })
            else:
                stats["by_tank"][tank[1]].append({
                    "name":tank[0],
                    "battles":tank[2],
                    "avgDmg":tank[3],
                    "dmgRank":GetRank(tank[3], settings.options["DMG_BREAKS"]),
                    "hitPercent":tank[5],
                    "hitPercentRank":GetRank(tank[5], settings.options["HIT_PERCENT_BREAKS"])
                })
        query = '''
        SELECT
            avgDmg,
            HTDmg,
            MTDmg,
            LTSpots,
            TDDmg,
            SPGDmg,
            updated_at
        FROM StatHistory WHERE account_id = ?
        ORDER BY updated_at DESC
        '''
        cur.execute(query, [account_id])
        for hist in [x for x in cur.fetchall()]:
            stats["history"].append({
                "overall":{
                    "dmg":hist[0],
                    "rank":GetRank(hist[0], settings.options["DMG_BREAKS"])
                },
                "HT":{
                    "dmg":hist[1],
                    "rank":GetRank(hist[1], settings.options["DMG_BREAKS"])
                },
                "MT":{
                    "dmg":hist[2],
                    "rank":GetRank(hist[2], settings.options["DMG_BREAKS"])
                },
                "LT":{
                    "spots":hist[3],
                    "rank":GetRank(hist[3], settings.options["SPOT_BREAKS"])
                },
                "TD":{
                    "dmg":hist[4],
                    "rank":GetRank(hist[4], settings.options["DMG_BREAKS"])
                },
                "SPG":{
                    "dmg":hist[5],
                    "rank":GetRank(hist[5], settings.options["DMG_BREAKS"])
                },
                "updated":hist[6]
            })
        # update the history dictionary by adding in the changes between each pair of stats
        # we need to iterate through each pair of stats - so stop 1 less than the length
        for x in range(len(stats["history"])-1):
            # slice the stats based on x - we want 2 in each slice
            # they should be sorted by date already - 0 index is most recent
            stat_comp = stats["history"][0+x:2+x]

            # iterate through each of the keys
            # just specify the dict here - it's easier than if-elsing to find the LT key
            for k,v in {
                            "overall":"dmg",
                            "HT":"dmg",
                            "MT":"dmg",
                            "LT":"spots",
                            "TD":"dmg",
                            "SPG":"dmg"
                        }.items():
                # don't bother if the older stat doesn't have anything for this type
                if stat_comp[0][k][v] is not None:
                    new = stat_comp[0][k][v]
                    old = stat_comp[1][k][v]

                    # add a key to the new dict based on the total change
                    stats["history"][x][k]['diff'] = new-old
    return stats

# Gets a list of tanks owned by the provided player
def GetPlayerTanks(account_id):
    with database.GetConnection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT tank_id, moe FROM MemberStats where account_id = ?', [account_id])
        return {k:v for k,v in cur.fetchall()}

def GetAllTanks(tier, ids=None):
    with database.GetConnection() as conn:
        cur = conn.cursor()
        if ids is None:
            query = "SELECT tank_id FROM Tanks WHERE tier = ?"
            cur.execute(query, [tier])
        else:
            id_list = ','.join([str(x) for x in ids])
            query = "SELECT * FROM Tanks WHERE tier = ? OR tank_id IN (?)"
            cur.execute(query, [tier, id_list])
        return cur.fetchall()

# Gets entries from the MOE Table
# If the 'date_confirmed' field is empty, then the player has not been compensated, and
# we do a quick calculation using the settings file to see what the player is owed.
def GetMOEHistory():
    ret_val = {
        "to_pay":[],
        "log":[]
    }
    with database.GetConnection() as conn:
        cur = conn.cursor()
        query = '''
        SELECT
        	nickname,
        	Tanks.name,
        	achv_type,
        	old_val,
        	new_val,
        	date_reached,
        	date_confirmed,
            Tanks.meta,
            payout,
            MOEHistory.rowid
        FROM MOEHistory
        	JOIN Members ON Members.account_id = MOEHistory.account_id
        	JOIN Tanks ON Tanks.tank_id = MOEHistory.tank_id
        ORDER BY date_confirmed, date_reached
        '''
        cur.execute(query)
        for hist in cur.fetchall():
            hist = list(hist)
            # if this player hasn't been marked as paid yet
            payout = 0
            if hist[6] is None:
                # is this a tank purchase?
                if hist[2] == "tank":
                    if hist[7] < 4: # no payouts for meta 4 or 5 tanks
                        payout_base = settings.options["PAYOUT_MULTIPLIERS"]["Purchase"]
                        meta_mutiplier = settings.options["PAYOUT_BY_META"][hist[7]-1]
                        payout = int(round(payout_base * meta_mutiplier,0))
                elif hist[2] == "moe": # payout for MOE gain
                    if hist[4] == 1: payout_base = settings.options["PAYOUT_MULTIPLIERS"]["1st Mark"]
                    elif hist[4] == 2: payout_base = settings.options["PAYOUT_MULTIPLIERS"]["2nd Mark"]
                    elif hist[4] == 3: payout_base = settings.options["PAYOUT_MULTIPLIERS"]["3rd Mark"]
                    else: raise Exception("Unknown indicator in MOEHistory(new_val): {}".format(hist[4]))
                    meta_mutiplier = settings.options["PAYOUT_BY_META"][hist[7]-1]
                    payout = int(round(payout_base * meta_mutiplier,0))
                else:
                    raise Exception("Unknown Achievement type in MOEHistory: {}".format(hist[2]))
            hist.append(payout)
            if hist[6] is None:
                ret_val["to_pay"].append(hist)
            else:
                ret_val["log"].append(hist)
    return ret_val

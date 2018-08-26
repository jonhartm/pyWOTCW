from flask import Flask, render_template, request
import sys, os
from os import path, getenv
from dotenv import load_dotenv

import settings
import database
import sqlite3 as sqlite

app = Flask(__name__)

load_dotenv()

# DMG_BREAKS = [1200, 1350, 1400, 1500]
# SPOT_BREAKS = [2,4,6,8]
# ATTENDANCE_BREAKS = [.2,.4,.6,.8]

# if not path.isfile(".env"):
#     raise Exception("Missing .env file...")
# else:
#     if getenv("WG_APP_ID") is None:
#         raise Exception("Missing .env Setting: 'WG_APP_ID'")
#     if getenv("CLAN_ID") is None:
#         raise Exception("Missing .env Setting: 'CLAN_ID'")

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
        	SPGDmg
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
                    "rank":GetRank(p[2], settings.DMG_BREAKS)
                }

            if p[3] is not None:
                player['HT'] = {
                    "dmg":p[3],
                    "rank":GetRank(p[3], settings.DMG_BREAKS)
                }
            if p[4] is not None:
                player['MT'] = {
                    "dmg":p[4],
                    "rank":GetRank(p[4], settings.DMG_BREAKS)
                }
            if p[5] is not None:
                player['LT'] = {
                    "spot":p[5],
                    "rank":GetRank(p[5], settings.SPOT_BREAKS)
                }
            if p[6] is not None:
                player['TD'] = {
                    "dmg":p[6],
                    "rank":GetRank(p[6], settings.DMG_BREAKS)
                }
            if p[7] is not None:
                player['SPG'] = {
                    "dmg":p[7],
                    "rank":GetRank(p[7], settings.DMG_BREAKS)
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
        	ROUND(spotting*1.0/battles, 2) AS avgSpotting
        FROM MemberStats
        	JOIN Tanks ON MemberStats.tank_id = Tanks.tank_id
        WHERE account_id = ?
        ORDER BY type, damage_dealt
        '''
        cur.execute(query, [account_id])
        for tank in [x for x in cur.fetchall()]:
            if tank[1] == "lightTank":
                stats["by_tank"][tank[1]].append({
                    "name":tank[0],
                    "battles":tank[2],
                    "avgSpot":tank[4],
                    "spotRank":GetRank(tank[4], settings.SPOT_BREAKS)
                })
            else:
                stats["by_tank"][tank[1]].append({
                    "name":tank[0],
                    "battles":tank[2],
                    "avgDmg":tank[3],
                    "dmgRank":GetRank(tank[3], settings.DMG_BREAKS)
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
        '''
        cur.execute(query, [account_id])
        for hist in [x for x in cur.fetchall()]:
            stats["history"].append({
                "overall":{
                    "dmg":hist[0],
                    "rank":GetRank(hist[0], settings.DMG_BREAKS)
                },
                "HT":{
                    "dmg":hist[1],
                    "rank":GetRank(hist[1], settings.DMG_BREAKS)
                },
                "MT":{
                    "dmg":hist[2],
                    "rank":GetRank(hist[2], settings.DMG_BREAKS)
                },
                "LT":{
                    "spots":hist[3],
                    "rank":GetRank(hist[3], settings.SPOT_BREAKS)
                },
                "TD":{
                    "dmg":hist[4],
                    "rank":GetRank(hist[4], settings.DMG_BREAKS)
                },
                "SPG":{
                    "dmg":hist[5],
                    "rank":GetRank(hist[5], settings.DMG_BREAKS)
                },
                "updated":hist[6]
            })
    return stats

@app.route('/')
def index():
    return render_template(
        "index.html",
        players=GetStats()
        )

@app.route('/player/<account_id>', methods=['GET', 'POST'])
def player(account_id):
    nickname = None
    with database.GetConnection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT nickname FROM Members WHERE account_id = ?", [account_id])
        nickname = cur.fetchone()[0]
    stats = GetIndivStats(account_id)
    return render_template(
        "player.html",
        name=nickname,
        tank_stats=stats["by_tank"],
        stat_hist=stats["history"]
        )


if __name__=="__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "-reset":
            if len(sys.argv) > 2:
                if sys.argv[2] == "-tanks":
                    database.ResetTanks(True)
            else:
                if input("This will reset the entire database - are you sure? (y/n): ").lower() == "y":
                    database.InitializeAll()

        elif sys.argv[1] == "-update":
            print("Updating database...")
            database.UpdateClanMembers()
        elif sys.argv[1] == "-stats":
            if len(sys.argv) == 3:
                print(GetIndivStats(sys.argv[2]))
            else:
                print(GetStats())
        else:
            pass # test functions here
    else:
        app.run(debug=True)

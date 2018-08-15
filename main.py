from flask import Flask, render_template, request
import sys, os
from os import path
from dotenv import load_dotenv

import secrets
import database
import sqlite3 as sqlite

app = Flask(__name__)

load_dotenv()

ROOT = path.dirname(path.realpath(__file__))

DMG_BREAKS = [1200, 1350, 1400, 1500]
SPOT_BREAKS = [2,4,6,8]
ATTENDANCE_BREAKS = [.2,.4,.6,.8]

def GetStats():
    stats = {}
    with sqlite.connect(path.join(ROOT, "wotcw.db")) as conn:
        cur = conn.cursor()
        query = '''
        SELECT
        	nickname,
        	Tanks.type,
        	ROUND((SELECT SUM(damage_dealt)/SUM(battles) FROM MemberStats WHERE account_id = Members.account_id AND battles > 0)) AS OverallAvgDmg,
        	SUM(damage_dealt)/SUM(battles) as AvgDmg,
        	ROUND(SUM(spotting)*1.0/SUM(battles),1) as AvgSpot,
            Members.attendance,
	        Members.following_calls,
            Members.account_id
        FROM MemberStats
        	JOIN Tanks on Tanks.tank_id = MemberStats.tank_id
        	JOIN Members on Members.account_id = MemberStats.account_id
        GROUP BY Tanks.type, nickname
        HAVING battles > 0
        ORDER BY nickname
        '''
        cur.execute(query)
        for row in cur:
            # make sure there's a key for this player
            if row[0] not in stats:
                stats[row[0]] = {}
            stats[row[0]]["OverallAvgDmg"] = row[2]
            stats[row[0]]["OverallAvgDmgRank"] = GetRank(row[2], DMG_BREAKS)
            stats[row[0]][row[1]] = GetTankStats(row)
            stats[row[0]]["Attendance"] = row[5]
            stats[row[0]]["Following_Calls"] = row[6]
            stats[row[0]]["account_id"] = row[7]
    return stats

def GetTankStats(row):
    ret_dict = {
        "AvgDmg": row[3],
        "AvgDmgRank": GetRank(row[3], DMG_BREAKS),
        "Spots": row[4],
        "SpotsRank": GetRank(row[4], SPOT_BREAKS)
    }
    return ret_dict

def GetRank(value, breaks):
    for rank in range(len(breaks)):
        if value < breaks[rank]:
            return rank + 1
    return 5


@app.route('/')
def index():
    member_data = []
    with sqlite.connect(path.join(ROOT, "wotcw.db")) as conn:
        cur = conn.cursor()
        query = "SELECT * FROM Members"
        cur.execute(query)
        for row in cur: member_data.append(row)

    return render_template(
        "index.html",
        members=GetStats()
        )

@app.route('/player/<account_id>', methods=['GET', 'POST'])
def player(account_id):
    return render_template(
        "player.html"
        )


if __name__=="__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "-reset":
            if sys.argv[2] == "-all":
                database.InitializeAll()
            elif sys.argv[2] == "-tanks":
                database.ResetTanks()
            elif sys.argv[2] == "-members":
                database.ResetClanMembers()
        elif sys.argv[1] == "-update":
            database.GetMemberTankStats(sys.argv[2])
        else:
            print(GetStats())
    else:
        app.run(debug=True)

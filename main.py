from flask import Flask, render_template, request
import sys, os
from os import path, getenv
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

# if not path.isfile(".env"):
#     raise Exception("Missing .env file...")
# else:
#     if getenv("WG_APP_ID") is None:
#         raise Exception("Missing .env Setting: 'WG_APP_ID'")
#     if getenv("CLAN_ID") is None:
#         raise Exception("Missing .env Setting: 'CLAN_ID'")

def GetStats():
    stats = {}
    with sqlite.connect(path.join(ROOT, "wotcw.db")) as conn:
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
        ORDER BY nickname
        '''
        for p in [x for x in cur.execute(query)]:
            player = {
                "nickname":p[1]
            }

            if p[2] is not None:
                player['overall'] = {
                    "dmg":p[2],
                    "rank":GetRank(p[2], DMG_BREAKS)
                }

            if p[3] is not None:
                player['HT'] = {
                    "dmg":p[3],
                    "rank":GetRank(p[3], DMG_BREAKS)
                }
            if p[4] is not None:
                player['MT'] = {
                    "dmg":p[4],
                    "rank":GetRank(p[4], DMG_BREAKS)
                }
            if p[5] is not None:
                player['LT'] = {
                    "dmg":p[5],
                    "rank":GetRank(p[5], SPOT_BREAKS)
                }
            if p[6] is not None:
                player['TD'] = {
                    "dmg":p[6],
                    "rank":GetRank(p[6], DMG_BREAKS)
                }
            if p[7] is not None:
                player['SPG'] = {
                    "dmg":p[7],
                    "rank":GetRank(p[7], DMG_BREAKS)
                }
            stats[p[0]] = player
    return stats

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
        players=GetStats()
        )

@app.route('/player/<account_id>', methods=['GET', 'POST'])
def player(account_id):
    return render_template(
        "player.html"
        )


if __name__=="__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "-reset":
            if input("This will reset the entire database - are you sure? (y/n): ").lower() == "y":
                database.InitializeAll()
        elif sys.argv[1] == "-update":
            print("Updating database...")
            database.UpdateClanMembers()
        else:
            print(GetStats())
    else:
        app.run(debug=True)

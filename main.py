from flask import Flask, render_template, request, make_response
import sys, os
from os import path, getenv
from dotenv import load_dotenv

import settings
import database
import json
import get_stats as stats
import sqlite3 as sqlite
from util import *

load_dotenv()

app = Flask(__name__)
app.secret_key = getenv("FLASK_SECRET_KEY")

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

@app.route('/')
def index():
    return render_template(
        "index.html",
        players=stats.GetStats()
        )

@app.route('/player/<account_id>', methods=['GET', 'POST'])
def player(account_id):
    nickname = None
    with database.GetConnection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT nickname FROM Members WHERE account_id = ?", [account_id])
        nickname = cur.fetchone()[0]
    indv_stats = stats.GetIndivStats(account_id)
    return render_template(
        "player.html",
        name=nickname,
        tank_stats=indv_stats["by_tank"],
        stat_hist=indv_stats["history"]
        )

@app.route('/meta_tanks', methods=['GET', 'POST'])
def meta_tanks():
    tank_list = getDictFromListWithIndex(stats.GetAllTanks(10, [16161]), 4)
    return render_template(
        "set_meta_tanks.html",
        tank_list = tank_list
        )

@app.route('/set_meta_tanks', methods=['POST'])
def set_meta_tanks():
    data = request.get_json()
    resp = make_response(json.dumps(data))
    try:
        settings.Set("META_TANK_RANKS", data)
        database.UpdateTankMetaRanks()
        resp.status_code = 200
    except Exception as e:
        resp.status = "AAA"
        resp.status_code = 400
    return resp

@app.route('/marks')
def marks():
    return render_template(
        'marks.html',
        moe_stats = stats.GetMOEHistory()

    )

if __name__=="__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "-reset":
            if len(sys.argv) > 2:
                if sys.argv[2] == "-tanks":
                    database.ResetTanks(True)
                elif sys.argv[2] == "-stats":
                    database.ResetMemberStats()
                elif sys.argv[2] == "-marks":
                    database.ResetMOEHistory()
            else:
                if input("This will reset the entire database - are you sure? (y/n): ").lower() == "y":
                    database.InitializeAll()

        elif sys.argv[1] == "-update":
            if len(sys.argv) > 2:
                if sys.argv[2] == "-skipMOE":
                    database.UpdateClanMembers(True)
            else:
                print("Updating database...")
                database.UpdateClanMembers()
        elif sys.argv[1] == "-stats":
            if len(sys.argv) == 3:
                print(stats.GetIndivStats(sys.argv[2]))
            else:
                print(stats.GetStats())
        else:
            print(stats.GetMOEHistory())

    else:
        app.run(debug=True)

from flask import Flask, render_template, request
import sys, os
from os import path, getenv
from dotenv import load_dotenv

import settings
import database
import get_stats as stats
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
                print(stats.GetIndivStats(sys.argv[2]))
            else:
                print(stats.GetStats())
        else:
            pass # test functions here
    else:
        app.run(debug=True)

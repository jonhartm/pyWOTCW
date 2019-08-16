from flask import Flask, render_template, request, make_response
import argparse, os, sys, json
from os import path, getenv
from dotenv import load_dotenv

import settings
import database
from update import *
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
    sorted_tanklist = {}
    for tanks in tank_list:
        tanks = list(tanks)
        tanks[1] = sorted(tanks[1], key=lambda x: ([-ord(c) for c in x[2]], x[3]))
        sorted_tanklist[tanks[0]] = tanks[1]
    return render_template(
        "set_meta_tanks.html",
        tank_list = sorted_tanklist
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

@app.route('/mark_payment', methods=['POST'])
def mark_payment():
    data = request.get_json()
    database.MarkMOEPayment(data["id"], data["payout"])
    resp = make_response(json.dumps(data))
    return resp

@app.route('/define_settings')
def define_settings():
    return render_template(
        'settings.html',
        options = settings.options
    )

# create the parser object
parser = argparse.ArgumentParser(
    description="RDDT WoT Stats",
    epilog="Run without arguments for Flask application"
    )

arg_group = parser.add_mutually_exclusive_group()

# command line arguments
arg_group.add_argument("-reset",
    nargs='*',
    help = "Drop one or more tables and recreate. WARNING: Will cause data loss.",
    choices = ["tanks", "stats", "marks", "all"])
arg_group.add_argument("-update",
    nargs='?',
    const="all",
    help = "Update the database",
    choices = ["skipMOE", "all"])
arg_group.add_argument("-delete",
    nargs=1,
    help = "Delete specific sets of data from the SQL Database.",
    choices = ["LastUpdate"])
arg_group.add_argument("-stats", nargs=1, help = "Retrieve stats on a particular item in the database.")
arg_group.add_argument("-test", nargs=1, help = "For use with testing. Probably doesn't do anything.")
arg_group.add_argument("-flask", help = "Start the flask application on a local machine.", action='store_true')
arg_group.add_argument("-update_app", help = "Update the application to a newer version.", action='store_true')

args = parser.parse_args()

if args.reset != None:
    if 'all' in args.reset:
        if query_yes_no("This will reset all tables in the database. Are you sure?"):
            database.InitializeAll()
    else:
        if query_yes_no("This will reset the following tables: {}. Are you sure?".format(', '.join([t.upper() for t in args.reset]))):
            if 'tanks' in args.reset:
                database.ResetTanks(True)
            if 'stats' in args.reset:
                database.ResetMemberStats()
            if 'marks' in args.reset:
                database.ResetMOEHistory()
elif args.update != None:
    if 'all' in args.update:
        database.UpdateClanMembers()
    if 'skipMOE' in args.update:
        database.UpdateClanMembers(True)
elif args.delete != None:
    if 'LastUpdate' in args.delete:
        database.DeleteLastUpdate()
        print("Last Update Removed")
elif args.stats != None:
    print(json.dumps(stats.GetIndivStats(args.stats[0]), indent=2))
elif args.update_app:
    check_for_update()
elif args.test != None:
    print("None")
elif args.flask:
    app.run(debug=True)

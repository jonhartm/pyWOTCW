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

def GetStats():
    stats = {}
    with sqlite.connect(path.join(ROOT, "wotcw.db")) as conn:
        cur = conn.cursor()
        query = '''
        SELECT
        	nickname,
        	Tanks.type,
        	SUM(battles),
        	SUM(damage_dealt)/SUM(battles) as AvgDmg,
        	ROUND(SUM(spotting)*1.0/SUM(battles),1) as AvgSpot
        FROM MemberStats
        	JOIN Tanks on Tanks.tank_id = MemberStats.tank_id
        	JOIN Members on Members.account_id = MemberStats.account_id
        GROUP BY Tanks.type, nickname
        '''
        cur.execute(query)
        for row in cur:
            if row[0] not in stats:
                stats[row[0]] = {}
            stats[row[0]][row[1]] = row[2:5]
    return stats


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
            pass
    else:
        app.run(debug=True)

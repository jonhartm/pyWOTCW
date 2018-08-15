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
        members=member_data
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
        else:
            pass
    else:
        app.run(debug=True)

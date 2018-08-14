from flask import Flask, render_template, request
import sys, os
from dotenv import load_dotenv

import secrets
from clan_details import *

app = Flask(__name__)

load_dotenv()

@app.route('/')
def index():
    Clan = ClanDetails()

    return render_template(
        "index.html",
        members=Clan.members
        )

if __name__=="__main__":
    if len(sys.argv) > 1:
        pass
    else:
        app.run(debug=True)

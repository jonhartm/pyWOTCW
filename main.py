from flask import Flask, render_template, request
import sys

import secrets
from clan_details import *

app = Flask(__name__)

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

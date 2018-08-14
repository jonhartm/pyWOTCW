import sys, os
from caching import *
from dotenv import load_dotenv
import datetime as dt

class ClanDetails():
    def __init__(self):
        ClanDetailsCache = CacheFile('ClanDetails.json')
        url = "https://api.worldoftanks.com/wgn/clans/info/"
        params = {
            "application_id": os.getenv("WG_APP_ID"),
            "clan_id": os.getenv("CLAN_ID"),
            "game": "wot"
        }
        API_data =  ClanDetailsCache.CheckCache_API(url, params, max_age=dt.timedelta(hours=23))
        self.name = API_data['data'][os.getenv("CLAN_ID")]['tag']
        self.members = []
        # count = 0
        for member_data in API_data['data'][os.getenv("CLAN_ID")]["members"]:
            # m = ClanMember(member_data['account_name'], member_data['account_id'])
            self.members.append(member_data['account_name'])

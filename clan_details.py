import sys, os
from caching import *
import datetime as dt

class ClanDetails():
    def __init__(self):
        ClanDetailsCache = CacheFile('ClanDetails.json')
        url = "https://api.worldoftanks.com/wgn/clans/info/"
        params = {
            "application_id": os.getenv("WG_APP_ID"),
            "clan_id": os.getenv("CLAN_ID"),
            "fields": "name, tag, members, members.role, members.account_id, members.account_name",
            "game": "wot"
        }
        API_data =  ClanDetailsCache.CheckCache_API(url, params, max_age=dt.timedelta(hours=23))
        self.name = API_data['data'][os.getenv("CLAN_ID")]['tag']
        self.members = []
        for member_data in API_data['data'][os.getenv("CLAN_ID")]["members"]:
            self.members.append(member_data)

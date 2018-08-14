from caching import *
import secrets

from clan_member import *

class ClanDetails():
    def __init__(self):
        ClanDetailsCache = CacheFile('ClanDetails.json')
        url = "https://api.worldoftanks.com/wgn/clans/info/"
        params = {
            "application_id": secrets.WG_APP_ID,
            "clan_id": secrets.CLAN_ID,
            "game": "wot"
        }
        API_data =  ClanDetailsCache.CheckCache_API(url, params)
        self.name = API_data['data'][secrets.CLAN_ID]['tag']
        self.members = []
        # count = 0
        for member_data in API_data['data'][secrets.CLAN_ID]["members"]:
            # m = ClanMember(member_data['account_name'], member_data['account_id'])
            self.members.append(member_data['account_name'])

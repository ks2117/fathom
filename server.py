import flask



class RiotApiHandler:

    def __init__(self, api_key, region):
        self.api_key = api_key

    def get_account(self, puuid):
        pass

    def get_account(self, tagLine, gameName):
        pass
    
    def get_champion_mastery(self, encryptedSummonerId):
        pass
    
    def get_champion_mastery(self, encryptedSummonerId, champion):
        pass

    def get_champion_mastery_sum(self, encryptedSummonerId):
        pass

    def get_active_clash_players(self, summonerId):
        pass

    def get_clash_team(self, teamId):
        pass
    
    def get_active_clash_tournaments(self):
        pass

    def get_active_clash_tournaments(self, teamId):
        pass

    def get_clash_tournament(self, tournamentId):
        pass

    def get_all_league_entries(self, queue, tier, division):
        pass

    def get_challenger_league(self, queue):
        pass

    def get_leagues_by_summoner(self, encryptedSummonerId):
        pass

    def get_league_entries(self, queue, tier, division):
        pass

    def get_grandmaster_league(self, queue):
        pass

    def get_league(self, leagueId):
        pass

    def get_master_league(self, queue):
        pass

    def get_platform_status(self):
        pass

    def get_match(self, matchId):
        pass

    def get_match_list(self, encryptedAccountId, championIds, queues, endTime, beginTime, endIndex, beginIndex):
        pass

    def get_match_timeline(self, matchId):
        pass

    def get_match_ids(self, tournamentCode):
        pass

    def get_match(self, matchId, tournamentCode):
        pass

    def get_summoner_by_account(self, encryptedAccountId):
        pass

    def get_summoner_by_name(self, summonerName):
        pass

    def get_summoner_by_puuid(self, puuid):
        pass

    def get_summoner_by_summoner(self, encryptedSummonerId):
        pass

    def get_third_party_code(self, encryptedSummonerId):
        pass

    def post_tournament_codes_stub(self, count, tournamentId, tournamentCodeParams):
        pass

    def get_lobby_events_stub(self, tournamentCode):
        pass

    def post_tournament_provider_stub(self, providerRegistrationParams):
        pass

    def post_tournament_id_stub(self, tournamentRegistrationParams):
        pass
    
    def post_tournament_codes(self, count, tournamentId, tournamentCodeParams):
        pass

    def get_tournament_dto(self, tournamentCode):
        pass
    
    def put_tournament_dto(self, tournamentCode):
        pass

    def get_lobby_events(self, tournamentCode):
        pass

    def post_tournament_provider(self, providerRegistrationParams):
        pass

    def post_tournament_id(self, tournamentRegistrationParams):
        pass
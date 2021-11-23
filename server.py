import flask
import os
import json
import csv
import pandas as pd
import requests

dirname = os.path.dirname(__file__)

class PlayerDatabase:

    def __init__(self):
        self.columns = ["puuid", "summonerId", "summonerName", "region", "tier", "division", "leaguePoints"]
        self.data = pd.DataFrame(columns=self.columns)


class RiotApiHandler:

    def __init__(self, routing_region=None, api_key=None):
        """
        Initialises the riot api handler for a particular api key


        Parameters: 
            routing_region (RoutingRegion): default cluster to execute the commands against
            api_key (str): riot developer api key
        """
        self.api_key_header = "X-Riot-Token"
        if api_key is None:
            filename = os.path.join(dirname, 'riot-api-key.txt')
            with open(filename) as f:
                self.api_key = f.read()
        else:
            self.api_key = api_key

        servers_filename = os.path.join(dirname, 'constants/servers.json')
        tiers_filename = os.path.join(dirname, 'constants/tiers.csv')
        divisions_filename = os.path.join(dirname, 'constants/divisions.csv')
        leagues_filename = os.path.join(dirname, 'constants/leagues.csv')
        regions_filename = os.path.join(dirname, 'constants/regions.csv')
        with open(servers_filename) as f:
            data = json.load(f)
            self.servers = [d['server'] for d in data]
        with open(tiers_filename) as f:
            self.tiers = f.read().split(",")
        with open(divisions_filename) as f:
            self.divisions = f.read().split(",")
        with open(leagues_filename) as f:
            self.leagues = f.read().split(",")
        with open(regions_filename) as f:
            self.regions = {r: r for r in f.read().split(",")}

        if routing_region is None:
            self.routing_region = self.regions['EUROPE']
        else:
            self.routing_region = routing_region

    def get_account(self, puuid):
        """
        Returns an account given a puuid.

        Parameters:
            puuid (str): puuid associated with the requested account

        Returns:
            puuid (str):
            gameName (str):
            tagLine (str):
            responseCode (int): https error code
            responseMsg (str): response message
        """
        pass

    def get_account(self, tagLine, gameName):
        """
        Returns an account given a puuid.

        Parameters:
            puuid (str): puuid associated with the requested account
            routingRegion (str): region to execute the command against.

        Returns:
            puuid (str):
            gameName (str):
            tagLine (str):
        """
        pass
    
    def get_champion_mastery(self, encryptedSummonerId, region):
        """
        Returns  a list of champion mastery scores for a given account

        Parameters:
            encryptedSummonerId (std): encrypted summoner ID
            region (Region): region to execute the command against

        Returns:
            [
                {
                    championId (int): champion ID
                    championLevel (int): mastery level
                    championPoints (int): mastery points on a chamion
                    lastPlayTime (time): last time played in epoch milliseconds
                    championPointsSinceLastLevel (int): mastery points gained since leveling up champion mastery
                    championPointsUntilNextLevel (int): points required to increase the mastery level
                    chestGranted (bool): whether a chest has been granted for getting S on a champion
                    tokensEarned (int): number of tokens earned for the purpose of leveling the mastery
                    encryptedSummonerId (str): encrypted summoner id
                }
            ]
        """
        pass
    
    def get_champion_mastery(self, encryptedSummonerId, championId, region):
        """
        Returns  champion mastery score for a given championID

        Parameters:
            encryptedSummonerId (std): encrypted summoner ID
            region (Region): region to execute the command against

        Returns:
            {
                championId (int): champion ID
                championLevel (int): mastery level
                championPoints (int): mastery points on a chamion
                lastPlayTime (time): last time played in epoch milliseconds
                championPointsSinceLastLevel (int): mastery points gained since leveling up champion mastery
                championPointsUntilNextLevel (int): points required to increase the mastery level
                chestGranted (bool): whether a chest has been granted for getting S on a champion
                tokensEarned (int): number of tokens earned for the purpose of leveling the mastery
                encryptedSummonerId (str): encrypted summoner id
            }
        """
        pass

    def get_champion_mastery_sum(self, encryptedSummonerId, region):
        pass

    def get_active_clash_players(self, summonerId, region):
        pass

    def get_clash_team(self, teamId, region):
        pass
    
    def get_active_clash_tournaments(self, region):
        pass

    def get_active_clash_tournaments(self, teamId, region):
        pass

    def get_clash_tournament(self, tournamentId, region):
        pass

    def get_all_league_entries(self, queue, tier, division, region):
        pass

    def get_challenger_league(self, queue, region):
        url = "https://" + region + ".api.riotgames.com/lol/league/v4/challengerleagues/by-queue/" + queue
        r = requests.get(url=url, headers={self.api_key_header: self.api_key})
        return r

    def get_leagues_by_summoner(self, encryptedSummonerId, region):
        pass

    def get_league_entries(self, queue, tier, division, region):
        pass

    def get_grandmaster_league(self, queue, region):
        pass

    def get_league(self, leagueId, region):
        pass

    def get_master_league(self, queue, region):
        pass

    def get_ranked_players(self):

        playerbase = pd.DataFrame()
        for q in self.leagues:
            for s in self.servers:
                self.get_challenger_league(q, s)
                # TODO: debug only
                break
                self.get_grandmaster_league(q, s)
                self.get_master_league(q, s)
                for t in self.tiers:
                    for d in self.divisions:
                        self.get_league_entries(q, t, d, s)

        pass

    def get_platform_status(self, region):
        pass

    def get_match(self, matchId, region):
        pass

    def get_match_list(self, encryptedAccountId, championIds, queues, endTime, beginTime, endIndex, beginIndex, region):
        pass

    def get_match_timeline(self, matchId, region):
        pass

    def get_tournament_match_ids(self, tournamentCode, region):
        pass

    def get_tournament_match(self, matchId, tournamentCode, region):
        pass

    def get_summoner_by_account(self, encryptedAccountId, region):
        pass

    def get_summoner_by_name(self, summonerName, region):
        pass

    def get_summoner_by_puuid(self, puuid, region):
        pass

    def get_summoner_by_summoner(self, encryptedSummonerId, region):
        pass

    def get_third_party_code(self, encryptedSummonerId, region):
        pass

    def post_tournament_codes_stub(self, count, tournamentId, tournamentCodeParams, region):
        pass

    def get_lobby_events_stub(self, tournamentCode, region):
        pass

    def post_tournament_provider_stub(self, providerRegistrationParams, region):
        pass

    def post_tournament_id_stub(self, tournamentRegistrationParams, region):
        pass
    
    def post_tournament_codes(self, count, tournamentId, tournamentCodeParams, region):
        pass

    def get_tournament_dto(self, tournamentCode, region):
        pass
    
    def put_tournament_dto(self, tournamentCode, region):
        pass

    def get_lobby_events(self, tournamentCode, region):
        pass

    def post_tournament_provider(self, providerRegistrationParams, region):
        pass

    def post_tournament_id(self, tournamentRegistrationParams, region):
        pass
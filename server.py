import flask
import os
import json
import csv
import pandas as pd
import requests
import time
from collections import deque

dirname = os.path.dirname(__file__)

class PlayerDatabase:

    def __init__(self, riotApiHandler=None):
        self.columns = ["region", "tier", "puuid", "rank", "summonerId", "summonerName", "leaguePoints"]
        self.data = pd.DataFrame(columns=self.columns)
        if riotApiHandler is None:
            self.riotApiHandler = RiotApiHandler()
        else:
            self.riotApiHandler = riotApiHandler

    def add(self, league, region):
        data = pd.DataFrame([[""] + [""] + [p[c] for c in self.columns[3:]] for p in league], columns=self.columns)
        for i, p in enumerate(league.entries):
            data.iloc[i].puuid = self.riotApiHandler.get_summoner_by_summoner(p.summonerName)
            data.iloc[i].region = region
            data.iloc[i].tier = league.tier
        self.data.append(data)


class RiotApiHandler:

    def __init__(self, default_routing_region=None, api_key=None, api_key_limits="development", limits_margin=0.05):
        """
        Initialises the riot api handler for a particular api key


        Parameters: 
            default_routing_region (RoutingRegion): default cluster to execute the commands against
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

        if default_routing_region is None:
            self.default_routing_region = self.regions['EUROPE']
        else:
            self.default_routing_region = default_routing_region

        if api_key_limits == "development":
            # Development limits are 20 requests/1s and 100 requests/120s (2 minutes)
            self.api_key_limits = {1: 20, 12000: 100}
        elif api_key_limits == "production":
            # Production limits are 500 requests/10s and 30000 requests/600s (10 minutes)
            self.api_key_limits = {10: 500, 600: 30000}
        else:
            self.api_key_limits = api_key_limits

        self.limits = {}
        self.limits_margin = limits_margin

    def apply_limiter(self, request, route=None, app=None, method=None, service=None):
        got_response = False
        while not got_response:
            ready = False
            while not ready:
                ready = True
                wait_time = 0
                if route is not None:
                    if route in self.limits:
                        while len(self.limits[route].timestamps) > 0 and\
                                self.limits[route].timestamps[0] < time.time() - self.limits[route].limit_period:
                            self.limits[route].timestamps.popleft()
                        limit = self.limits[route].limit * (1 - self.limits_margin) - 1
                        if limit <= len(self.limits[route].timestamps):
                            ready = False
                            timestamp = self.limits[route].timestamps[-limit]
                            wait_time = max(wait_time, self.limits[route].limit_period - (time.time() - timestamp))
                    else:
                        self.limits[route] = {"limit": -1, "limit_period": -1, "timestamps": deque()}
                if app is not None:
                    if app in self.limits:
                        while len(self.limits[app].timestamps) > 0 and\
                                self.limits[app].timestamps[0] < time.time() - self.limits[app].limit_period:
                            self.limits[app].timestamps.popleft()
                        limit = self.limits[app].limit * (1 - self.limits_margin) - 1
                        if limit <= len(self.limits[app].timestamps):
                            ready = False
                            timestamp = self.limits[app].timestamps[-limit]
                            wait_time = max(wait_time, self.limits[app].limit_period - (time.time() - timestamp))
                    else:
                        self.limits[app] = {"limit": -1, "limit_period": -1, "timestamps": deque()}
                if method is not None:
                    if method in self.limits:
                        while len(self.limits[method].timestamps) > 0 and\
                                self.limits[method].timestamps[0] < time.time() - self.limits[method].limit_period:
                            self.limits[method].timestamps.popleft()
                        limit = self.limits[method].limit * (1 - self.limits_margin) - 1
                        if limit <= len(self.limits[method].timestamps):
                            ready = False
                            timestamp = self.limits[method].timestamps[-limit]
                            wait_time = max(wait_time, self.limits[method].limit_period - (time.time() - timestamp))
                    else:
                        self.limits[method] = {"limit": -1, "limit_period": -1, "timestamps": deque()}
                if service is not None:
                    if service in self.limits:
                        while len(self.limits[service].timestamps) > 0 and\
                                self.limits[service].timestamps[0] < time.time() - self.limits[service].limit_period:
                            self.limits[service].timestamps.popleft()
                        limit = self.limits[service].limit * (1 - self.limits_margin) - 1
                        if limit <= len(self.limits[service].timestamps):
                            ready = False
                            timestamp = self.limits[service].timestamps[-limit]
                            wait_time = max(wait_time, self.limits[service].limit_period - (time.time() - timestamp))
                    else:
                        self.limits[service] = {"limit": -1, "limit_period": -1, "timestamps": deque()}
                time.sleep(wait_time)

            timestamp = time.time()
            resp = request.send()
            got_response = True
            if self.limits[route].limit == -1:
                pass
            if self.limits[app].limit == -1:
                pass
            if self.limits[method].limit == -1:
                pass
            if self.limits[service].limit == -1:
                pass
        return resp

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
        req = requests.Request('GET', url, headers={self.api_key_header: self.api_key})
        self.apply_limiter(region, req)
        return req

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
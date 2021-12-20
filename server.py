import flask
import os
import json
import csv
import pandas as pd
import requests
import time
from collections import deque
import re

dirname = os.path.dirname(__file__)

class PlayerDatabase:

    def __init__(self, riotApiHandler=None, save_path=os.path.join(dirname, "playerbase/data.csv")):
        if riotApiHandler is None:
            self.riotApiHandler = RiotApiHandler()
        else:
            self.riotApiHandler = riotApiHandler
        self.save_path=save_path
        self.columns = ["region", "puuid", "summonerId", "summonerName"]
        for q in self.riotApiHandler.leagues:
            self.columns = self.columns + [q + "_tier", q + "_rank", q + "_leaguePoints", q + "_wins", q + "_losses",
                                           q + "_history"]
        self.data = pd.DataFrame(columns=self.columns)
        self.history_columns = ["timestamp", "tier", "rank", "leaguePoints", "wins", "losses"]

    def add(self, league, region):
        print(str.format("[{}] ADDING {} PLAYERS", time.time(), len(league["entries"])))
        for i, p in enumerate(league["entries"]):
            player_data = self.riotApiHandler.get_summoner_by_summoner(p["summonerId"], region=region)
            ranked_data = self.riotApiHandler.get_leagues_by_summoner(p["summonerId"], region=region)
            puuid = player_data["puuid"]
            ranked_data = {d["queueType"]: d for d in ranked_data}
            if len(self.data.index) > 0:
                id = (self.data["puuid"].values == puuid).argmax()
            else:
                id = -1
            if id > 0 or id == 0 and self.data.loc[0, puuid] == puuid:
                self.data.loc[id, "region"] = region
                self.data.loc[id, "summonerId"] = p["summonerId"]
                self.data.loc[id, "summonerName"] = player_data["name"]
                for q in self.riotApiHandler.leagues:
                    self.data.loc[id, q + "_tier"] = ranked_data[q]["tier"]
                    self.data.loc[id, q + "_rank"] = ranked_data[q]["rank"]
                    self.data.loc[id, q + "_leaguePoints"] = ranked_data[q]["leaguePoints"]
                    self.data.loc[id, q + "_wins"] = ranked_data[q]["wins"]
                    self.data.loc[id, q + "_losses"] = ranked_data[q]["losses"]
                    self.data.loc[id, q + "_history"]\
                        .append(pd.DataFrame([[time.time()] + [ranked_data[q][c] for c in self.history_columns if "timestamp" not in c]],
                                           columns=self.history_columns))
            else:
                new_player = pd.DataFrame([["" if "history" not in c else pd.DataFrame([], columns=self.history_columns)
                                            for c in self.columns]], columns=self.columns)
                new_player["region"] = region
                new_player["summonerId"] = p["summonerId"]
                new_player["summonerName"] = player_data["name"]
                for q in self.riotApiHandler.leagues:
                    if q in ranked_data:
                        new_player.loc[0, q + "_tier"] = ranked_data[q]["tier"]
                        new_player.loc[0, q + "_rank"] = ranked_data[q]["rank"]
                        new_player.loc[0, q + "_leaguePoints"] = ranked_data[q]["leaguePoints"]
                        new_player.loc[0, q + "_wins"] = ranked_data[q]["wins"]
                        new_player.loc[0, q + "_losses"] = ranked_data[q]["losses"]
                        new_player.loc[0, q + "_history"].append(pd.DataFrame([[time.time()] + [ranked_data[q][c]\
                                for c in self.history_columns if "timestamp" not in c]], columns=self.history_columns))
                self.data.append(new_player, ignore_index=True)

            print(str.format("[{}] ADDED {}/{} PLAYERS", time.time(), i, len(league["entries"])))

    def save(self, path=None):
        if path is None:
            self.data.to_csv(self.save_path)
        else:
            self.data.to_csv(path)

    def load(self, path=None):
        if path is None and os.path.exists(self.save_path):
            self.data = pd.read_csv(self.save_path)
        elif path is not None and os.path.exists(path):
            self.data = pd.read_csv(path)


class LimitTracker:

    def __init__(self, limits, timestamps=deque(), limits_margin=0.05):
        self.limits = [{"limit_period": l["limit_period"], "limit": l["limit"], "timestamps": timestamps} for l in limits]
        self.limits_margin = limits_margin

    def get_wait_time(self):
        wait_time = 0
        for l in self.limits:
            while len(l["timestamps"]) > 0 and l["timestamps"][0] < time.time() - l["limit_period"]:
                l["timestamps"].popleft()
            limit = int(l["limit"] * (1 - self.limits_margin) - 1)
            if limit <= len(l["timestamps"]):
                wait_time = max(wait_time, l["limit_period"]) #  - (time.time() - l["timestamps"][-limit])
        return wait_time

    def add(self, timestamp):
        for l in self.limits:
            l["timestamps"].append(timestamp)

class RiotApiHandler:

    def __init__(self, app_name="fathom", default_routing_region=None, api_key=None, api_key_limits="development", limits_margin=0.05):
        """
        Initialises the riot api handler for a particular api key


        Parameters: 
            default_routing_region (RoutingRegion): default cluster to execute the commands against
            api_key (str): riot developer api key
        """
        self.app_name = app_name
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

            #TODO: I dont like that change of types
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
        self.session = requests.Session()

    def apply_limiter(self, request, route=None, app=None, method=None):
        got_response = False
        print(str.format("[{}]: SENT REQUEST: {}", time.time(), request.url))
        while not got_response:
            ready = False
            while not ready:
                ready = True
                wait_time = 0
                if route is not None:
                    if route in self.limits:
                        wait_time = max(self.limits[route].get_wait_time(), wait_time)
                    else:
                        self.limits[route] = None
                if app is not None:
                    if app in self.limits:
                        wait_time = max(self.limits[app].get_wait_time(), wait_time)
                    else:
                        self.limits[app] = None
                if method is not None:
                    if method in self.limits:
                        wait_time = max(self.limits[method].get_wait_time(), wait_time)
                    else:
                        self.limits[method] = None
                time.sleep(wait_time)

            resp = self.session.send(request)
            timestamp = time.time()
            print(str.format("[{}]: GOT RESPONSE TO REQUEST: {}, RESP_CODE: {}", time.time(), request.url, resp.status_code))
            if resp.status_code != 429:
                # 429 is "exceeded rate limiter", all other responses to be handled outside this function
                got_response = True
            app_limits = list(map(int, re.split("[,:]", resp.headers["X-App-Rate-Limit"])))
            app_limits_counts = list(map(int, re.split("[,:]", resp.headers["X-App-Rate-Limit-Count"])))
            method_limits = list(map(int, re.split("[,:]", resp.headers["X-Method-Rate-Limit"])))
            method_limits_counts = list(map(int, re.split("[,:]", resp.headers["X-Method-Rate-Limit-Count"])))
            if self.limits[route] is None:
                self.limits[route] = \
                    LimitTracker([{"limit_period": l, "limit": self.api_key_limits[l], "timestamps": deque([timestamp])}
                                  for l in self.api_key_limits.keys()])
            if self.limits[app] is None:
                self.limits[app] = \
                    LimitTracker([{"limit_period": app_limits[2 * i + 1], "limit": app_limits[2 * i], "timestamps": deque([timestamp])}
                                  for i in range(len(app_limits) // 2)])
            if self.limits[method] is None:
                self.limits[method] = \
                    LimitTracker([{"limit_period": method_limits[2 * i + 1], "limit": method_limits[2 * i], "timestamps": deque([timestamp])}
                                  for i in range(len(method_limits) // 2)])

            self.limits[route].add(timestamp)
            self.limits[app].add(timestamp)
            self.limits[method].add(timestamp)
            if not got_response:
                max_wait_time = 1
                for i, a in enumerate(app_limits):
                    if i % 2 == 0 and a <= app_limits_counts[i]:
                        max_wait_time = max(max_wait_time, app_limits[i + 1])
                for i, m in enumerate(method_limits):
                    if i % 2 == 0 and m <= method_limits_counts[i]:
                        max_wait_time = max(max_wait_time, method_limits[i + 1])
                print(str.format("[{}] APP_LIMITS: {}, APP_LIMIT_COUNTS: {}, METHOD_LIMIT: {}, METHOD_LIMIT_COUNTS: {}",
                                 time.time(), app_limits, app_limits_counts, method_limits, method_limits_counts))
                time.sleep(max_wait_time)
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
        req = requests.Request('GET', url, headers={self.api_key_header: self.api_key}).prepare()
        resp = self.apply_limiter(req, route=region, app=self.app_name,
                                  method="lol/league/v4/challengerleagues/by-queue/")
        return json.loads(resp.content)

    def get_leagues_by_summoner(self, encryptedSummonerId, region):
        url = "https://" + region + ".api.riotgames.com/lol/league/v4/entries/by-summoner/" + encryptedSummonerId
        req = requests.Request('GET', url, headers={self.api_key_header: self.api_key}).prepare()
        resp = self.apply_limiter(req, route=region, app=self.app_name, method="lol/league/v4/entries/by-summoner/")
        return json.loads(resp.content)

    def get_league_entries(self, queue, tier, division, region):
        pass

    def get_grandmaster_league(self, queue, region):
        pass

    def get_league(self, leagueId, region):
        pass

    def get_master_league(self, queue, region):
        pass

    def get_ranked_players(self):

        playerbase = PlayerDatabase()
        playerbase.load()
        for q in self.leagues:
            for s in self.servers:
                league = self.get_challenger_league(q, s)
                playerbase.add(league, s)
                playerbase.save()
                print(playerbase.data)
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
        url = "https://" + region + ".api.riotgames.com/lol/summoner/v4/summoners/" + encryptedSummonerId
        req = requests.Request('GET', url, headers={self.api_key_header: self.api_key}).prepare()
        resp = self.apply_limiter(req, route=region, app=self.app_name, method="lol/summoner/v4/summoners/")
        return json.loads(resp.content)

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

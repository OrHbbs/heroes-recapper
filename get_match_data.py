import pprint
import struct
from collections import defaultdict

from heroprotocol.versions import protocol92264 as protocol
from datetime import datetime, timedelta
import json
import time
import re

import utils
from utils import default_wanted_keys, get_as_str


def get_match_type(match_type: int):
    pass


def get_datetime(utc_time: int, timezone: int = 0):
    sec = (utc_time + timezone) / 10000000

    epoch = datetime(1601, 1, 1)
    dt = epoch + timedelta(seconds=sec)

    return str(dt.replace(microsecond=0))


def get_player_data(unfiltered_data: dict, num_players: int, wanted_keys: list[str] = default_wanted_keys):
    """
    :param num_players: this should usually be 10
    :param unfiltered_data: the dict of data from replay.tracker.events
    :param wanted_keys: a list of the keys that should be parsed from the data. The default values are defined in
    utils.py. Modify or create a new list of strings if you want to process more or less columns of data
    :return: a dictionary containing player details of all the players in the match
    """

    details = {
        "duration": None,
        "player_details": [{} for _ in range(num_players)]
    }

    for instance in unfiltered_data['m_instanceList']:
        for value_list in instance['m_values']:
            if value_list:
                details["duration"] = value_list[0]['m_time']
                break

    for instance in unfiltered_data['m_instanceList']:
        metric_name = instance['m_name']

        if metric_name in wanted_keys:

            for i, value_list in enumerate(instance['m_values']):
                if i < num_players:
                    if value_list:
                        details['player_details'][i][metric_name] = value_list[0]['m_value']

    return details


def parse_battlelobby(battlelobby, players):
    """Gets useful information out of battlelobby"""

    battletag_pattern = re.compile(rb'([\w\-\.\#\x80-\xFF]+#[0-9]{4,5})')

    battletags = battletag_pattern.finditer(battlelobby)

    i = 0
    party_num = 0
    prev_byte_sequence = None

    for match in battletags:
        battletag = match.group(0).decode('utf-8', errors='ignore')

        start_pos = match.start()
        end_pos = match.end()

        # lvl info is stored in the 4 bytes after the battletag, in big-endian
        account_level_bytes = battlelobby[end_pos:end_pos + 4]
        account_level = struct.unpack('>I', account_level_bytes)[0]

        # party info is stored in the 8 bytes before the battletag
        party_byte_sequence = battlelobby[start_pos - 8:start_pos - 1]

        players[i]["battletag"] = battletag
        players[i]["accountLevel"] = account_level

        if party_byte_sequence.startswith(b'\x00@'):
            players[i]["party"] = 0
        elif party_byte_sequence != prev_byte_sequence:  # different party detected
            party_num += 1
            players[i]["party"] = party_num
        else:
            players[i]["party"] = party_num

        prev_byte_sequence = party_byte_sequence

        i += 1

        if i == 5:
            party_num = 2

    if party_num >= 5:
        print("warning in parse_battlelobby, invalid party detected")
        print(players)

    return


def parse_replay(path: str, create_json: bool = True, check_duplicate: bool = False, sorted_dict=None):
    print(path)

    if sorted_dict is None:
        sorted_dict = {}
    import mpyq

    mpyq = mpyq.MPQArchive(path)

    details = protocol.decode_replay_details(mpyq.read_file('replay.details'))

    if check_duplicate is False or details['m_timeUTC'] not in sorted_dict:

        initdata = protocol.decode_replay_initdata(mpyq.read_file('replay.initdata'))
        attribute_events = protocol.decode_replay_attributes_events(mpyq.read_file('replay.attributes.events'))
        game_mode = initdata['m_syncLobbyState']['m_gameDescription']['m_gameOptions']['m_ammId']
        battlelobby = mpyq.read_file('replay.server.battlelobby')
        bans = initdata['m_syncLobbyState']

        print(initdata['m_syncLobbyState']['m_gameDescription']['m_gameType'])

        # for i in initdata['m_syncLobbyState']['m_gameDescription']['m_gameType']:
        #     print(i)

        # for i in initdata['m_syncLobbyState']:
        #     for j in initdata['m_syncLobbyState'][i]:
        #         print(j)

        # for event in attribute_events:
        #     print("Source:", event.get('source'))
        #     print("MapNamespace:", event.get('mapNamespace'))
        #     print("Scopes:", event.get('scopes'))
        #     print("\n")

        # parsing customs for now
        if game_mode is None:
            print("parsing customs for now")
            game_mode = -1
            # return {}

        header = protocol.decode_replay_header(mpyq.header['user_data_header']['content'])
        build_number = header['m_version']['m_baseBuild']

        module_name = 'heroprotocol.protocol{}'.format(build_number)

        print(module_name)

        tracker_events = protocol.decode_replay_tracker_events(mpyq.read_file('replay.tracker.events'))

        player_list = details['m_playerList']

        # pprint.pp(player_list)

        version = (f"{header['m_version']['m_major']}."
                   f"{header['m_version']['m_minor']}."
                   f"{header['m_version']['m_revision']}."
                   f"{header['m_version']['m_build']}")

        del details['m_playerList']

        timezone_offset = details['m_timeLocalOffset']

        # For inserting data into a json or dataframe, add the row to database.py as well
        output = {
            'rawDate': details['m_timeUTC'],
            'date': get_datetime(details['m_timeUTC'], timezone=timezone_offset),
            'version': version,
            'map': get_as_str(details['m_title']),
            # 'winner': get_as_str(tracker_events),
            'gameMode': utils.game_mode_strings[game_mode],
            'duration': None,
            # 'firstToTen':
            # 'firstFort':
            'draftOrder': ["", "", "", "", "", "", "", "", "", ""],
            'bansBlue': ["", "", ""],
            'bansRed': ["", "", ""],
            'firstPick': None,
        }

        players = []

        team1 = []
        team2 = []

        for player in player_list:

            for key, value in player.items():
                if type(value) is bytes:
                    player[key] = get_as_str(value)

            player_output = {
                'name': player['m_name'],
                'hero': player['m_hero'],
                'result': player['m_result'],
                'teamId': player['m_teamId']
            }

            # todo what happens if there are observers in the game? what teamId are they on, if they appear in the game?
            team1.append(player_output) if player_output['teamId'] == 0 else team2.append(player_output)

        players = team1 + team2

        if len(players) < 10:
            return {}

        parse_battlelobby(battlelobby, players)

        output['players'] = players

        events_data = {}

        # converting data to non-bytes

        current_line = 0

        bans_blue_indices = [0, 12, 60]  # hero names are kept in the first line, and on every 6th line after that
        bans_red_indices = [6, 18, 54]
        draft_order_indices = [24, 30, 36, 42, 48, 66, 72, 78, 84, 90]

        for event in tracker_events:

            for key, value in event.items():
                event[key] = get_as_str(value)

            events_data.update(event)

            if event['_event'] in ['NNet.Replay.Tracker.SHeroBannedEvent', 'NNet.Replay.Tracker.SHeroPickedEvent']:
                for vals in event:
                    line_value = utils.get_shortname_by_altname(event[vals])

                    if current_line in bans_blue_indices:
                        output["bansBlue"][bans_blue_indices.index(current_line)] = line_value
                    elif current_line in bans_red_indices:
                        output["bansRed"][bans_red_indices.index(current_line)] = line_value
                    elif current_line in draft_order_indices:
                        output["draftOrder"][draft_order_indices.index(current_line)] = line_value
                    elif current_line == 1:
                        output["firstPick"] = line_value

                    current_line += 1

        game_stats = get_player_data(events_data, len(player_list))

        # todo game time is different on heroesprofile and stats of the storm, which one is correct?
        output['duration'] = game_stats['duration']  # in seconds

        for i in range(len(player_list)):
            output['players'][i].update(game_stats['player_details'][i])

        if create_json:
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=4)

        return output

    return {}

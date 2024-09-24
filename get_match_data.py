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

        # print(game_mode)

        # not parsing customs for now
        if game_mode is None:
            print("not parsing customs for now")
            return {}

        header = protocol.decode_replay_header(mpyq.header['user_data_header']['content'])
        build_number = header['m_version']['m_baseBuild']

        module_name = 'heroprotocol.protocol{}'.format(build_number)

        print(module_name)

        tracker_events = protocol.decode_replay_tracker_events(mpyq.read_file('replay.tracker.events'))

        player_list = details['m_playerList']

        patch = (f"{header['m_version']['m_major']}."
                 f"{header['m_version']['m_minor']}."
                 f"{header['m_version']['m_revision']}."
                 f"{header['m_version']['m_build']}")

        del details['m_playerList']

        timezone_offset = details['m_timeLocalOffset']

        # For inserting data into a json or dataframe, add the row to database.py as well
        output = {
            'rawDate': details['m_timeUTC'],
            'date': get_datetime(details['m_timeUTC'], timezone=timezone_offset),
            'map': get_as_str(details['m_title']),
            # 'winner': get_as_str(tracker_events),
            'gameMode': utils.game_mode_strings[game_mode],
            'duration': None,
            # 'firstToTen':
            # 'firstFort':
            'bansBlue': ["", "", ""],
            'bansRed': ["", "", ""],
            'firstPick': None,
            'pickOrder': ""
        }

        players = []
        for player in player_list:

            for key, value in player.items():
                if type(value) is bytes:
                    player[key] = get_as_str(value)

            player_output = {
                'name': player['m_name'],
                'hero': player['m_hero'],
                'result': player['m_result'],
                # 'team': player['m_teamId']
            }

            players.append(player_output)

        parse_battlelobby(battlelobby, players)

        output['players'] = players

        events_data = {}

        # converting data to non-bytes

        b_line = 0

        for event in tracker_events:

            for key, value in event.items():
                event[key] = get_as_str(value)

            events_data.update(event)

            if event['_event'] == 'NNet.Replay.Tracker.SHeroBannedEvent':
                for vals in event:
                    match b_line:
                        case 0:  # hero name is kept the first line, and on every 6th line after that
                            output["bansBlue"][0] = utils.get_shortname_by_altname(event[vals])
                        case 1:  # second line is the team who banned the first hero, and subsequently the team with fp
                            output["firstPick"] = (event[vals])
                        case 6:
                            output["bansRed"][0] = utils.get_shortname_by_altname(event[vals])
                        case 12:
                            output["bansBlue"][1] = utils.get_shortname_by_altname(event[vals])
                        case 18:
                            output["bansRed"][1] = utils.get_shortname_by_altname(event[vals])
                        case 24:
                            output["bansRed"][2] = utils.get_shortname_by_altname(event[vals])
                        case 30:
                            output["bansBlue"][2] = utils.get_shortname_by_altname(event[vals])

                    b_line += 1

        game_stats = get_player_data(events_data, len(player_list))

        # todo game time is different on heroesprofile and stats of the storm, which one is correct?
        output['duration'] = game_stats['duration']

        for i in range(len(player_list)):
            output['players'][i].update(game_stats['player_details'][i])

        if create_json:
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=4)

        return output

    return {}

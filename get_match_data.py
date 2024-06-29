from heroprotocol.versions import protocol92264 as protocol
from datetime import datetime, timedelta
import json
from itertools import islice
import time

from utils import default_wanted_keys, get_as_str


def get_match_type(match_type: int):
    pass


def get_datetime(utc_time: int):
    # assuming time in nanoseconds
    # todo this assumption is wrong
    sec = utc_time / 1_000_000_000

    epoch = datetime(1970, 1, 1)
    dt = epoch + timedelta(seconds=sec)
    return str(dt)


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


def parse_replay(path: str, create_json: bool = True):
    import mpyq

    mpyq = mpyq.MPQArchive(path)

    header = protocol.decode_replay_header(mpyq.header['user_data_header']['content'])
    build_number = header['m_version']['m_baseBuild']

    module_name = 'heroprotocol.protocol{}'.format(build_number)

    print(module_name)

    details = protocol.decode_replay_details(mpyq.read_file('replay.details'))
    tracker_events = protocol.decode_replay_tracker_events(mpyq.read_file('replay.tracker.events'))
    header_info = protocol.decode_replay_header(mpyq.header['user_data_header']['content'])

    player_list = details['m_playerList']

    del details['m_playerList']

    # print(tracker_events)

    output = {
        'rawDate': details['m_timeUTC'],
        'date': get_datetime(details['m_timeUTC']),
        'map': get_as_str(details['m_title']),
        # 'winner': get_as_str(tracker_events),
        'duration': None,
        # 'firstToTen':
        # 'firstFort':
        #
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

    output['players'] = players

    events_data = {}

    # converting data to non-bytes
    for event in tracker_events:

        for key, value in event.items():
            event[key] = get_as_str(value)

        events_data.update(event)

    game_stats = get_player_data(events_data, len(player_list))

    #todo game time is different on heroesprofile and stats of the storm, which one is correct?
    output['duration'] = game_stats['duration']

    for i in range(len(player_list)):
        output['players'][i].update(game_stats['player_details'][i])

    if create_json:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=4)

    if True:
        with open('more-data.json', 'a', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=4)

    return output

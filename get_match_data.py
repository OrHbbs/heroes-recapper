from heroprotocol.versions import protocol92264 as protocol
from datetime import datetime, timedelta
import json

from utils import default_wanted_keys


def get_match_type(match_type):
    pass


def get_as_str(val):
    """
    :param val: a dictionary, list, byte, string, integer, or any combination of these
    :return: the same parameter except recursively turned into a string
    """
    if isinstance(val, dict):
        return {k: get_as_str(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [get_as_str(i) for i in val]
    elif isinstance(val, bytes):
        return val.decode('utf-8')
    else:
        return str(val)


def get_datetime(utc_time):
    # assuming time in nanoseconds
    # todo this assumption is wrong
    sec = utc_time / 1_000_000_000

    epoch = datetime(1970, 1, 1)
    dt = epoch + timedelta(seconds=sec)
    return str(dt)


def get_player_data(unfiltered_data, num_players, wanted_keys=default_wanted_keys):
    """

    :param wanted_keys: a list of the keys that should be parsed from the data. The default values to obtain is 
    defined in utils.py. Modify or create a new list of strings if you want to process more or less columns of data 
    :param num_players: this should usually be 10 
    :param unfiltered_data: the dict of data from replay.tracker.events 
    :return: a dictionary containing player details of all the players in the match
    """

    all_player_details = [{} for _ in range(num_players)]

    for instance in unfiltered_data['m_instanceList']:
        metric_name = instance['m_name']

        if metric_name in wanted_keys:

            for i, value_list in enumerate(instance['m_values']):
                if i < num_players:
                    if value_list:
                        all_player_details[i][metric_name] = value_list[0]['m_value']

    return all_player_details


def parse_replay(src, create_json=True):
    import mpyq

    mpyq = mpyq.MPQArchive(src)

    header = protocol.decode_replay_header(mpyq.header['user_data_header']['content'])
    build_number = header['m_version']['m_baseBuild']

    module_name = 'heroprotocol.protocol{}'.format(build_number)

    print(module_name)

    details = protocol.decode_replay_details(mpyq.read_file('replay.details'))
    tracker_events = protocol.decode_replay_tracker_events(
        mpyq.read_file('replay.tracker.events')
    )

    player_list = details['m_playerList']

    del details['m_playerList']

    output = {
        'rawDate': details['m_timeUTC'],
        'date': get_datetime(details['m_timeUTC']),
        'map': get_as_str(details['m_title'])
        # 'winner': get_as_str(tracker_events)
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

    for i in range(len(player_list)):
        output['players'][i].update(game_stats[i])

    if create_json:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=4)

    return output

# data = parse_replay('sky.StormReplay')


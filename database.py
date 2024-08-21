import json

from sortedcontainers import SortedDict
# import pandas as pd
import get_match_data

import utils

#todo: im using sortedcontainers instead of pandas dataframes. Might want to change this later

# def check_duplicate(df: pd.DataFrame, column_name: str, entry: int) -> bool:
#     """
#     A binary search to check if the replay is a duplicate in the database
#     todo: For now, sorted_column uses rawDate.
#     I can't really tell if there's anything better to use that uniquely identifies a StormReplay file, but if there is,
#     please let me know
#
#     :param df: a dataframe with a sorted column
#     :param column_name: sorted column's name
#     :param entry: the DF entry to check against
#     :return: true if there is a duplicate, false otherwise
#     """
#
#     low, high = 0, len(df) - 1
#
#     while low <= high:
#         mid = (low + high) // 2
#         mid_value = df.iloc[mid][column_name]
#
#         if mid_value < entry:
#             low = mid + 1
#         elif mid_value > entry:
#             high = mid - 1
#         else:
#             print("duplicate found")
#             return True
#
#     return False
#
#
# def sort_dataframe(df: pd.DataFrame, column: str):
#     """
#     :param df: dataframe
#     :param column:
#     :return:
#     """
#
#     return df.sort_values(by=[column]).reset_index(drop=True)
#
#
# def add_to_database(paths: list[str], matches_database: pd.DataFrame, create_json: bool = False):
#     """
#
#     :param paths: a list of strings containing the paths to all the replay files
#     :param matches_database: the current database
#     :param create_json: output a json file
#     :return: the updated database containing parsed replay info on the replays provided in paths
#     """
#
#     parsed_replays = []
#
#     for path in paths:
#         if not path.endswith(".StormReplay"):
#             print("unexpected file")
#             continue
#         data = get_match_data.parse_replay(path=path, create_json=create_json)
#
#         match_data = {
#             "rawDate": data["rawDate"],
#             "date": data["date"],
#             "map": data["map"],
#             "duration": data["duration"],
#             "levelRed": data["players"][0]["Level"],
#             "levelBlue": data["players"][-1]["Level"]
#         }
#
#         for each_player in data['players']:
#             del each_player['Level']
#
#         #todo This doesn't check for duplicates within the paths parameter.
#         # It's possible that different two files can have the exact same replay data
#         if check_duplicate(matches_database, "rawDate", match_data["rawDate"]):
#             continue
#
#         player_data_combined = {}
#
#         for i, player_data in enumerate(data['players']):
#             for key, value in player_data.items():
#                 player_data_combined[f"{i + 1}_{key}"] = value
#
#         match_data.update(player_data_combined)
#
#         parsed_replays.append(match_data)
#
#     match_df = pd.DataFrame(parsed_replays)
#
#     matches_database = pd.concat([match_df, matches_database], ignore_index=True)
#
#     return matches_database


def add_to_container(paths: list[str], sorted_dict: SortedDict, create_json: bool = False):
    for path in paths:
        if not path.endswith(".StormReplay"):
            print("unexpected file")
            continue
        data = get_match_data.parse_replay(path=path, create_json=create_json, check_duplicate=True,
                                           sorted_dict=sorted_dict)

        if len(data) == 0:
            continue

        raw_date = data["rawDate"]

        if raw_date not in sorted_dict:

            match_data = {
                "rawDate": raw_date,
                "date": data["date"],
                "map": data["map"],
                "duration": data["duration"],
                "gameMode": data["gameMode"],
                "levelRed": data["players"][0]["Level"],
                "levelBlue": data["players"][-1]["Level"]
            }

            for each_player in data['players']:
                del each_player['Level']

            player_data_combined = {}

            for i, player_data in enumerate(data['players']):
                for key, value in player_data.items():
                    player_data_combined[f"{i + 1}_{key}"] = value

            match_data.update(player_data_combined)

            sorted_dict[match_data["rawDate"]] = match_data

            # del match_data["rawDate"]

    return sorted_dict


def add_to_container_and_update_tables(paths: list[str], sorted_dict: SortedDict, recapper_dir: str, create_json: bool = False,
                                       hero_table=None, ):

    print(recapper_dir)

    if hero_table is None:
        try:
            with open(f"{recapper_dir}/hero_table.json", 'r') as f:
                hero_table = json.load(f)
        except FileNotFoundError:
            hero_table = utils.create_empty_hero_table()

    for path in paths:
        if not path.endswith(".StormReplay"):
            print("unexpected file")
            continue
        data = get_match_data.parse_replay(path=path, create_json=create_json, check_duplicate=True,
                                           sorted_dict=sorted_dict)

        if len(data) == 0:
            continue

        raw_date = data["rawDate"]

        if raw_date not in sorted_dict:

            match_data = {
                "rawDate": raw_date,
                "date": data["date"],
                "map": data["map"],
                "duration": data["duration"],
                "gameMode": data["gameMode"],
                "firstPick": data["firstPick"],
                "levelRed": data["players"][0]["Level"],
                "levelBlue": data["players"][-1]["Level"],
                "bansBlue": data["bansBlue"],
                "bansRed": data["bansRed"]
            }

            for each_player in data['players']:
                del each_player['Level']

            player_data_combined = {}

            for i, player_data in enumerate(data['players']):
                for key, value in player_data.items():
                    player_data_combined[f"{i + 1}_{key}"] = value

            match_data.update(player_data_combined)

            sorted_dict[match_data["rawDate"]] = match_data

            # print(match_data)

            # _______________________
            # updating hero_table

            # getting heroes in the game

            match_heroes = [0] * 10
            winner = match_data["1_result"]

            # used for talent stats - updated if both teams reach a certain talent tier
            min_level = int(min(match_data['levelRed'], match_data['levelBlue']))

            for i in range(1, 1 + len(match_heroes)):
                print(match_data[f"{i}_hero"])
                match_heroes[i - 1] = utils.get_id_by_hero(match_data[f"{i}_hero"])

                ht = hero_table[match_heroes[i - 1] - 1]

                # updating integer values

                ht['gamesPlayed'] += 1
                ht['totalDamage'] += int(match_data[f"{i}_HeroDamage"])
                ht['totalHealing'] += int(match_data[f"{i}_Healing"])
                ht['totalDamageSoaked'] += int(match_data[f"{i}_DamageSoaked"])
                ht['totalExperience'] += int(match_data[f"{i}_ExperienceContribution"])
                ht['totalSiege'] += int(match_data[f"{i}_SiegeDamage"])

                for j in range(1, 1 + len(ht['talentGames'])):
                    selected_talent = int(match_data[f"{i}_Tier{j}Talent"]) - 1
                    if selected_talent == -1:
                        break
                    ht['talentGames'][j - 1][selected_talent] += 1
                    if min_level >= int(utils.talent_tiers[j - 1]):
                        ht['talentNormalizedGames'][j - 1][selected_talent] += 1

            # updating ally and enemy hero games

            for i in range(5):
                for j in range(5):
                    if i != j:
                        hero_table[match_heroes[i] - 1]['allyHeroGames'][match_heroes[j] - 1] += 1
                        hero_table[match_heroes[i + 5] - 1]['allyHeroGames'][match_heroes[j + 5] - 1] += 1

                    hero_table[match_heroes[i] - 1]['enemyHeroGames'][match_heroes[j + 5] - 1] += 1
                    hero_table[match_heroes[i + 5] - 1]['enemyHeroGames'][match_heroes[j] - 1] += 1

                    # updating wins
                    if winner == 1:  # left/blue team wins
                        hero_table[match_heroes[i] - 1]['allyHeroWins'][match_heroes[j] - 1] += 1
                        hero_table[match_heroes[i] - 1]['enemyHeroWins'][match_heroes[j] - 1] += 1
                    else:  # right/red team wins
                        hero_table[match_heroes[i + 5] - 1]['enemyHeroWins'][match_heroes[j] - 1] += 1
                        hero_table[match_heroes[i + 5] - 1]['allyHeroWins'][match_heroes[j + 5] - 1] += 1

            # updating other conditional values based on the winner

            r1 = 1
            r2 = 6

            if winner == 2:
                r1 += 5
                r2 += 5

            for i in range(r1, r2):
                ht = hero_table[match_heroes[i - 1] - 1]
                ht['gamesWon'] += 1

                for j in range(1, 1 + len(ht['talentGames'])):
                    selected_talent = int(match_data[f"{i}_Tier{j}Talent"]) - 1

                    if selected_talent == -1:
                        break

                    ht['talentWins'][j - 1][selected_talent] += 1

                    # normalized talent wins

                    if min_level >= int(utils.talent_tiers[j - 1]):
                        ht['talentNormalizedWins'][j - 1][selected_talent] += 1

            # updating hero bans

            for i in range(len(match_data["bansBlue"])):
                match_ban_id = utils.get_id_by_hero(match_data["bansBlue"][i])

                hero_table[match_ban_id - 1]['gamesBanned'] += 1

            for i in range(len(match_data["bansRed"])):
                match_ban_id = utils.get_id_by_hero(match_data["bansRed"][i])

                hero_table[match_ban_id - 1]['gamesBanned'] += 1

        with open(f"{recapper_dir}/hero_table.json", "w") as outfile:
            json.dump(hero_table, outfile)

    return sorted_dict


def update_tables(replay_data):
    """
    opens hero-data.json and player-data.json and updates the values inside

    todo these should be aggregated into one json file later

    :param replay_data: the match data parsed, which is returned from get_match_data.parse_replay
    :return: None
    """

    with open('hero-data.json', 'w') as f:
        pass

    with open('player-data.json', 'w') as f:
        # check if player tag is part of any aliases
        # get the keys of the player tags
        # if the player key is found inside player-data
        # then update map winrate, hero winrate, talent winrate, ally winrate, enemy winrate

        pass

    return


# maybe this is inefficient
def get_nth_value(sorted_dict: SortedDict, i: int):
    if i < 0 or i >= len(sorted_dict):
        raise IndexError("Index out of range")
    keys = list(sorted_dict.keys())
    key = keys[i]
    return sorted_dict[key]


# def save_to_pickle(path, matches_database):
#     matches_database.to_pickle(path)
#
#
# def load_from_pickle(path):
#     return pd.read_pickle(path)
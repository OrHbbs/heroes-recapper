import math

from sortedcontainers import SortedDict
import pandas as pd
import get_match_data
import time

from utils import test_paths


def check_duplicate(df: pd.DataFrame, column_name: str, entry: int) -> bool:
    """
    A binary search to check if the replay is a duplicate in the database
    todo: For now, sorted_column uses rawDate.
    I can't really tell if there's anything better to use that uniquely identifies a StormReplay file, but if there is,
    please let me know

    :param df: a dataframe with a sorted column
    :param column_name: sorted column's name
    :param entry: the DF entry to check against
    :return: true if there is a duplicate, false otherwise
    """

    low, high = 0, len(df) - 1

    while low <= high:
        mid = (low + high) // 2
        mid_value = df.iloc[mid][column_name]

        if mid_value < entry:
            low = mid + 1
        elif mid_value > entry:
            high = mid - 1
        else:
            print("duplicate found")
            return True

    return False


def sort_dataframe(df: pd.DataFrame, column: str):
    """
    :param df: dataframe
    :param column:
    :return:
    """

    return df.sort_values(by=[column]).reset_index(drop=True)


def add_to_database(paths: list[str], matches_database: pd.DataFrame, create_json: bool = False):
    """

    :param paths: a list of strings containing the paths to all the replay files
    :param matches_database: the current database
    :param create_json: output a json file
    :return: the updated database containing parsed replay info on the replays provided in paths
    """

    parsed_replays = []

    for path in paths:
        if not path.endswith(".StormReplay"):
            print("unexpected file")
            continue
        data = get_match_data.parse_replay(path=path, create_json=create_json)

        match_data = {
            "rawDate": data["rawDate"],
            "date": data["date"],
            "map": data["map"],
            "duration": data["duration"],
            "levelRed": data["players"][0]["Level"],
            "levelBlue": data["players"][-1]["Level"]
        }

        for each_player in data['players']:
            del each_player['Level']

        #todo This doesn't check for duplicates within the paths parameter.
        # It's possible that different two files can have the exact same replay data
        if check_duplicate(matches_database, "rawDate", match_data["rawDate"]):
            continue

        player_data_combined = {}

        for i, player_data in enumerate(data['players']):
            for key, value in player_data.items():
                player_data_combined[f"{i + 1}_{key}"] = value

        match_data.update(player_data_combined)

        parsed_replays.append(match_data)

    match_df = pd.DataFrame(parsed_replays)

    matches_database = pd.concat([match_df, matches_database], ignore_index=True)

    return matches_database


def add_to_container(paths: list[str], sorted_dict: SortedDict, create_json: bool = False):

    for path in paths:
        if not path.endswith(".StormReplay"):
            print("unexpected file")
            continue
        data = get_match_data.parse_replay(path=path, create_json=create_json, check_duplicate=True, sorted_dict=sorted_dict)

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

            # print(match_data)

            sorted_dict[match_data["rawDate"]] = match_data

            # del match_data["rawDate"]

    return sorted_dict


# maybe this is inefficient
def get_nth_value(sorted_dict: SortedDict, i: int):
    if i < 0 or i >= len(sorted_dict):
        raise IndexError("Index out of range")
    keys = list(sorted_dict.keys())
    key = keys[i]
    return sorted_dict[key]

def save_to_pickle(path, matches_database):
    matches_database.to_pickle(path)


def load_from_pickle(path):
    return pd.read_pickle(path)


def test():
    replays = test_paths
    newDF = pd.DataFrame()

    start_time = time.time()
    newDF = add_to_database(replays, newDF, create_json=True)
    print(f"runtime: {time.time() - start_time}")

    newDF = sort_dataframe(newDF, "rawDate")
    print(newDF)

    save_to_pickle("a_pickle.pkl", newDF)


def test2():
    df = load_from_pickle("a_pickle.pkl")

    print(df)
    print(len(df.index))

    paths1 = ["test-data/infernal.StormReplay"]
    paths2 = test_paths

    df = add_to_database(paths=paths2, matches_database=df)

    # save_to_pickle("a_pickle.pkl", df)

    sort_dataframe(df, "rawDate")
    print(df)
    print(len(df.index))

import pandas as pd
import get_match_data
import time


def add_to_database(paths, matches_database):
    """

    :param paths: a list of strings containing the paths to all the replay files
    :param matches_database: the current database
    :return: the updated database containing parsed replay info on the replays provided in paths
    """

    parsed_replays = []

    for src in paths:
        data = get_match_data.parse_replay(src=src, create_json=False)

        match_data = {
            "rawDate": data["rawDate"],
            "date": data["date"],
            "map": data["map"]
        }

        player_data_combined = {}

        for i, player_data in enumerate(data['players']):
            for key, value in player_data.items():
                player_data_combined[f"{i + 1}_{key}"] = value

        match_data.update(player_data_combined)

        parsed_replays.append(match_data)

    match_df = pd.DataFrame(parsed_replays)

    matches_database = pd.concat([match_df, matches_database], ignore_index=True)

    return matches_database


replays = ["sky.StormReplay", "sample.StormReplay"]
newDF = pd.DataFrame()

start_time = time.time()
print(add_to_database(replays, newDF))
print(f"runtime: {time.time() - start_time}")

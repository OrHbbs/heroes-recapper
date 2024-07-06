import ijson
from sortedcontainers import SortedDict
from unidecode import unidecode
import string

default_wanted_keys = ['Takedowns', 'Deaths', 'TownKills', "SoloKill", 'Assists', "Level",
                       'TeamTakedowns', 'ExperienceContribution', 'Healing', "SiegeDamage", "StructureDamage",
                       'MinionDamage', 'HeroDamage', 'MercCampCaptures', 'SelfHealing', 'TimeSpentDead',
                       'TimeCCdEnemyHeroes', 'CreepDamage', 'SummonDamage', 'Tier1Talent', 'Tier2Talent', 'Tier3Talent',
                       'Tier4Talent', 'Tier5Talent', 'Tier6Talent', 'Tier7Talent', 'DamageTaken', 'DamageSoaked',
                       'HighestKillStreak', 'ProtectionGivenToAllies', 'TimeSilencingEnemyHeroes',
                       'TimeRootingEnemyHeroes', 'TimeStunningEnemyHeroes', 'ClutchHealsPerformed',
                       'EscapesPerformed', 'VengeancesPerformed', 'TeamfightEscapesPerformed', 'OutnumberedDeaths',
                       'TeamfightHealingDone', 'TeamfightDamageTaken', 'TeamfightHeroDamage', 'OnFireTimeOnFire',
                       'TimeOnPoint', 'CageUnlocksInterrupted', 'PhysicalDamage', 'SpellDamage', 'Multikill',
                       'MinionKills', 'RegenGlobes', 'TimeInTemple']

essential_keys = ['Takedowns', 'Deaths', 'TownKills', "SoloKill", 'Assists', "Level", 'TeamTakedowns',
                  'ExperienceContribution', 'Healing', "SiegeDamage", 'MinionDamage', 'HeroDamage', 'MercCampCaptures',
                  'SelfHealing', 'TimeSpentDead', 'TimeCCdEnemyHeroes', 'Tier1Talent', 'Tier2Talent', 'Tier3Talent',
                  'Tier4Talent', 'Tier5Talent', 'Tier6Talent', 'Tier7Talent', 'DamageTaken', 'PhysicalDamage',
                  'SpellDamage']

test_paths = ["test-data/sky.StormReplay", "test-data/sample0.StormReplay", "test-data/sample1.StormReplay",
             "test-data/sample2.StormReplay", "test-data/sample3.StormReplay", "test-data/sample4.StormReplay",
             "test-data/infernal.StormReplay"]

game_mode_strings = {
    50001: 'Quick Match',
    50021: 'Versus AI',
    50041: 'Practice',
    50031: 'Brawl',
    50051: 'Unranked Draft',
    50061: 'Hero League',
    50071: 'Team League',
    50091: 'Storm League',
    50101: 'ARAM',
    -1: 'Custom'
}


def clean_string(val: str, remove_spaces=False):
    """
    :param str: any string
    :return: the same string in lower case, without punctuation, and without special characters
    """
    if remove_spaces:
        return unidecode(val.lower()).translate(val.maketrans('', '', string.punctuation))
    return unidecode(val.lower()).translate(val.maketrans('', '', string.punctuation)).replace(" ", "")


def load_partial_json(path, max_entries=50):
    sorted_data = SortedDict()
    try:
        with open(path, 'r') as f:
            parser = ijson.items(f, '')
            entry_count = 0
            for entry in parser:
                if entry_count >= max_entries:
                    break
                if isinstance(entry, dict):
                    for key, value in entry.items():
                        if entry_count >= max_entries:
                            break
                        sorted_data[int(key)] = value
                        entry_count += 1
                else:
                    break

    except FileNotFoundError:
        pass

    return sorted_data


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


def get_winner(side: int):
    if side == 1:
        return "Blue"
    return "Red"
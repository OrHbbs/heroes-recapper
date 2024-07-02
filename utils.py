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

def clean_string(val: str):
    """
    :param str: any string
    :return: the same string in lower case, without punctuation, and without special characters
    """
    return unidecode(val.lower()).translate(val.maketrans('', '', string.punctuation))


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
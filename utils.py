import json
import ijson
import math
from sortedcontainers import SortedDict
from unidecode import unidecode
import string
import copy

default_wanted_keys = ['Deaths', 'TownKills', "SoloKill", 'Assists', "Level",
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

essential_keys = ['Deaths', 'TownKills', "SoloKill", 'Assists', "Level", 'TeamTakedowns',
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

map_ids = {
    1000: 'Alterac Pass',
    1001: 'Battlefield of Eternity',
    1002: 'Braxis Holdout',
    1003: 'Cursed Hollow',
    1004: 'Dragon Shire',
    1005: 'Garden of Terror',
    1006: 'Infernal Shrines',
    1007: 'Sky Temple',
    1008: 'Tomb of the Spider Queen',
    1009: 'Towers of Doom',
    1010: 'Volskaya Foundry',
    1100: 'Blackhearts Bay',
    1101: 'Haunted Mines',
    1102: 'Hanamura Temple',
    1103: 'Warhead Junction',
    2000: 'Braxis Outpost',
    2001: 'Industrial District',
    2002: 'Lost Cavern',
    2003: 'Silver City',
}

hero_ids = {
    1: 'abathur',
    2: 'alarak',
    3: 'alexstrasza',
    4: 'ana',
    5: 'anduin',
    6: 'anubarak',
    7: 'artanis',
    8: 'arthas',
    9: 'auriel',
    10: 'azmodan',
    11: 'blaze',
    12: 'brightwing',
    13: 'cassia',
    14: 'chen',
    15: 'cho',
    16: 'chromie',
    17: 'deathwing',
    18: 'deckard',
    19: 'dehaka',
    20: 'diablo',
    21: 'dva',
    22: 'etc',
    23: 'falstad',
    24: 'fenix',
    25: 'gall',
    26: 'garrosh',
    27: 'gazlowe',
    28: 'genji',
    29: 'greymane',
    30: 'guldan',
    31: 'hanzo',
    32: 'hogger',
    33: 'illidan',
    34: 'imperius',
    35: 'jaina',
    36: 'johanna',
    37: 'junkrat',
    38: 'kaelthas',
    39: 'kelthuzad',
    40: 'kerrigan',
    41: 'kharazim',
    42: 'leoric',
    43: 'lili',
    44: 'liming',
    45: 'ltmorales',
    46: 'lucio',
    47: 'lunara',
    48: 'maiev',
    49: 'malganis',
    50: 'malfurion',
    51: 'malthael',
    52: 'medivh',
    53: 'mei',
    54: 'mephisto',
    55: 'muradin',
    56: 'murky',
    57: 'nazeebo',
    58: 'nova',
    59: 'orphea',
    60: 'probius',
    61: 'qhira',
    62: 'ragnaros',
    63: 'raynor',
    64: 'rehgar',
    65: 'rexxar',
    66: 'samuro',
    67: 'sgthammer',
    68: 'sonya',
    69: 'stitches',
    70: 'stukov',
    71: 'sylvanas',
    72: 'tassadar',
    73: 'thebutcher',
    74: 'lostvikings',
    75: 'thrall',
    76: 'tracer',
    77: 'tychus',
    78: 'tyrael',
    79: 'tyrande',
    80: 'uther',
    81: 'valeera',
    82: 'valla',
    83: 'varian',
    84: 'whitemane',
    85: 'xul',
    86: 'yrel',
    87: 'zagara',
    88: 'zarya',
    89: 'zeratul',
    90: 'zuljin'
}

hero_data = [
    {
        'id': '1',
        'name': 'Abathur',
        'shortName': 'abathur',
        'alternativeName': '',
        'nickname': 'aba',
        'oldRole': 'Specialist',
        'role': 'Support',
        'attackType': 'Melee',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '2',
        'name': 'Alarak',
        'shortName': 'alarak',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Assassin',
        'role': 'Melee Assassin',
        'attackType': 'Melee',
        'releaseDate': '9/13/2016 12:00:00 AM'
    },
    {
        'id': '3',
        'name': 'Alexstrasza',
        'shortName': 'alexstrasza',
        'alternativeName': '',
        'nickname': 'alex',
        'oldRole': 'Support',
        'role': 'Healer',
        'attackType': 'Ranged',
        'releaseDate': '11/14/2017 12:00:00 AM'
    },
    {
        'id': '4',
        'name': 'Ana',
        'shortName': 'ana',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Support',
        'role': 'Healer',
        'attackType': 'Ranged',
        'releaseDate': '9/26/2017 12:00:00 AM'
    },
    {
        'id': '5',
        'name': 'Anduin',
        'shortName': 'anduin',
        'alternativeName': '',
        'oldRole': '',
        'nickname': '',
        'role': 'Healer',
        'attackType': 'Ranged',
        'releaseDate': '6/18/2019 12:00:00 AM'
    },
    {
        'id': '6',
        'name': 'Anub\'arak',
        'shortName': 'anubarak',
        'alternativeName': 'Anubarak',
        'nickname': 'anub',
        'oldRole': 'Warrior',
        'role': 'Tank',
        'attackType': 'Melee',
        'releaseDate': '3/18/2014 12:00:00 AM'
    },
    {
        'id': '7',
        'name': 'Artanis',
        'shortName': 'artanis',
        'alternativeName': '',
        'nickname': 'art',
        'oldRole': 'Warrior',
        'role': 'Bruiser',
        'attackType': 'Melee',
        'releaseDate': '10/20/2015 12:00:00 AM'
    },
    {
        'id': '8',
        'name': 'Arthas',
        'shortName': 'arthas',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Warrior',
        'role': 'Tank',
        'attackType': 'Melee',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '9',
        'name': 'Auriel',
        'shortName': 'auriel',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Support',
        'role': 'Healer',
        'attackType': 'Ranged',
        'releaseDate': '6/14/2016 12:00:00 AM'
    },
    {
        'id': '10',
        'name': 'Azmodan',
        'shortName': 'azmodan',
        'alternativeName': '',
        'nickname': 'azmo',
        'oldRole': 'Specialist',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '11',
        'name': 'Blaze',
        'shortName': 'blaze',
        'alternativeName': 'Firebat',
        'nickname': '',
        'oldRole': 'Warrior',
        'role': 'Tank',
        'attackType': 'Ranged',
        'releaseDate': '1/9/2018 12:00:00 AM'
    },
    {
        'id': '12',
        'name': 'Brightwing',
        'shortName': 'brightwing',
        'alternativeName': 'FaerieDragon',
        'nickname': 'bw',
        'oldRole': 'Support',
        'role': 'Healer',
        'attackType': 'Ranged',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '13',
        'name': 'Cassia',
        'shortName': 'cassia',
        'alternativeName': 'Amazon',
        'nickname': '',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '4/4/2017 12:00:00 AM'
    },
    {
        'id': '14',
        'name': 'Chen',
        'shortName': 'chen',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Warrior',
        'role': 'Bruiser',
        'attackType': 'Melee',
        'releaseDate': '4/7/2014 12:00:00 AM'
    },
    {
        'id': '15',
        'name': 'Cho',
        'shortName': 'cho',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Warrior',
        'role': 'Tank',
        'attackType': 'Melee',
        'releaseDate': '11/17/2015 12:00:00 AM'
    },
    {
        'id': '16',
        'name': 'Chromie',
        'shortName': 'chromie',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '5/17/2016 12:00:00 AM'
    },
    {
        'id': '17',
        'name': 'Deathwing',
        'shortName': 'deathwing',
        'alternativeName': '',
        'nickname': 'dw',
        'oldRole': '',
        'role': 'Bruiser',
        'attackType': 'Melee',
        'releaseDate': '11/12/2019 12:00:00 AM'
    },
    {
        'id': '18',
        'name': 'Deckard',
        'shortName': 'deckard',
        'alternativeName': '',
        'nickname': 'old man',
        'oldRole': 'Support',
        'role': 'Healer',
        'attackType': 'Ranged',
        'releaseDate': '4/24/2018 12:00:00 AM'
    },
    {
        'id': '19',
        'name': 'Dehaka',
        'shortName': 'dehaka',
        'alternativeName': '',
        'nickname': 'dino',
        'oldRole': 'Warrior',
        'role': 'Bruiser',
        'attackType': 'Melee',
        'releaseDate': '3/29/2016 12:00:00 AM'
    },
    {
        'id': '20',
        'name': 'Diablo',
        'shortName': 'diablo',
        'alternativeName': '',
        'nickname': 'dibbles',
        'oldRole': 'Warrior',
        'role': 'Tank',
        'attackType': 'Melee',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '21',
        'name': 'D.Va',
        'shortName': 'dva',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Warrior',
        'role': 'Tank',
        'attackType': 'Ranged',
        'releaseDate': '5/16/2017 12:00:00 AM'
    },
    {
        'id': '22',
        'name': 'E.T.C.',
        'shortName': 'etc',
        'alternativeName': 'L90ETC',
        'nickname': 'cow',
        'oldRole': 'Warrior',
        'role': 'Tank',
        'attackType': 'Melee',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '23',
        'name': 'Falstad',
        'shortName': 'falstad',
        'alternativeName': '',
        'nickname': 'fals,chicken',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '24',
        'name': 'Fenix',
        'shortName': 'fenix',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '4/24/2018 12:00:00 AM'
    },
    {
        'id': '25',
        'name': 'Gall',
        'shortName': 'gall',
        'nickname': '',
        'alternativeName': '',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '11/17/2015 12:00:00 AM'
    },
    {
        'id': '26',
        'name': 'Garrosh',
        'shortName': 'garrosh',
        'alternativeName': '',
        'nickname': 'garry',
        'oldRole': 'Warrior',
        'role': 'Tank',
        'attackType': 'Melee',
        'releaseDate': '8/8/2017 12:00:00 AM'
    },
    {
        'id': '27',
        'name': 'Gazlowe',
        'shortName': 'gazlowe',
        'alternativeName': 'Tinker',
        'nickname': 'gaz',
        'oldRole': 'Specialist',
        'role': 'Bruiser',
        'attackType': 'Melee',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '28',
        'name': 'Genji',
        'shortName': 'genji',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '4/25/2017 12:00:00 AM'
    },
    {
        'id': '29',
        'name': 'Greymane',
        'shortName': 'greymane',
        'alternativeName': '',
        'nickname': 'grey,gm',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '1/12/2016 12:00:00 AM'
    },
    {
        'id': '30',
        'name': 'Gul\'dan',
        'shortName': 'guldan',
        'alternativeName': 'Guldan',
        'nickname': '',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '8/2/2016 12:00:00 AM'
    },
    {
        'id': '31',
        'name': 'Hanzo',
        'shortName': 'hanzo',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '12/12/2017 12:00:00 AM'
    },
    {
        'id': '32',
        'name': 'Hogger',
        'shortName': 'hogger',
        'alternativeName': '',
        'nickname': 'hog',
        'oldRole': '',
        'role': 'Bruiser',
        'attackType': 'Melee',
        'releaseDate': '12/1/2020 12:00:00 AM'
    },
    {
        'id': '33',
        'name': 'Illidan',
        'shortName': 'illidan',
        'alternativeName': '',
        'nickname': 'illi',
        'oldRole': 'Assassin',
        'role': 'Melee Assassin',
        'attackType': 'Melee',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '34',
        'name': 'Imperius',
        'shortName': 'imperius',
        'alternativeName': '',
        'nickname': 'imp',
        'oldRole': 'Warrior',
        'role': 'Bruiser',
        'attackType': 'Melee',
        'releaseDate': '1/8/2019 12:00:00 AM'
    },
    {
        'id': '35',
        'name': 'Jaina',
        'shortName': 'jaina',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '12/2/2014 12:00:00 AM'
    },
    {
        'id': '36',
        'name': 'Johanna',
        'shortName': 'johanna',
        'alternativeName': 'Crusader',
        'nickname': 'joh,jo',
        'oldRole': 'Warrior',
        'role': 'Tank',
        'attackType': 'Melee',
        'releaseDate': '6/2/2015 12:00:00 AM'
    },
    {
        'id': '37',
        'name': 'Junkrat',
        'shortName': 'junkrat',
        'alternativeName': '',
        'nickname': 'junk,rat',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '10/17/2017 12:00:00 AM'
    },
    {
        'id': '38',
        'name': 'Kael\'thas',
        'shortName': 'kaelthas',
        'alternativeName': 'Kaelthas',
        'nickname': 'kael,kt',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '5/12/2015 12:00:00 AM'
    },
    {
        'id': '39',
        'name': 'Kel\'thuzad',
        'shortName': 'kelthuzad',
        'alternativeName': 'Kelthuzad',
        'nickname': 'ktz',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '10/24/2017 12:00:00 AM'
    },
    {
        'id': '40',
        'name': 'Kerrigan',
        'shortName': 'kerrigan',
        'alternativeName': '',
        'nickname': 'kerri',
        'oldRole': 'Assassin',
        'role': 'Melee Assassin',
        'attackType': 'Melee',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '41',
        'name': 'Kharazim',
        'shortName': 'kharazim',
        'alternativeName': 'Monk',
        'nickname': 'khara,monk',
        'oldRole': 'Support',
        'role': 'Healer',
        'attackType': 'Melee',
        'releaseDate': '8/18/2015 12:00:00 AM'
    },
    {
        'id': '42',
        'name': 'Leoric',
        'shortName': 'leoric',
        'alternativeName': '',
        'nickname': 'leo',
        'oldRole': 'Warrior',
        'role': 'Bruiser',
        'attackType': 'Melee',
        'releaseDate': '7/21/2015 12:00:00 AM'
    },
    {
        'id': '43',
        'name': 'Li Li',
        'shortName': 'lili',
        'alternativeName': 'LiLi',
        'nickname': '',
        'oldRole': 'Support',
        'role': 'Healer',
        'attackType': 'Ranged',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '44',
        'name': 'Li-Ming',
        'shortName': 'liming',
        'alternativeName': 'Wizard',
        'nickname': 'ming',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '2/2/2016 12:00:00 AM'
    },
    {
        'id': '45',
        'name': 'Lt. Morales',
        'shortName': 'ltmorales',
        'alternativeName': 'Medic',
        'nickname': 'medic',
        'oldRole': 'Support',
        'role': 'Healer',
        'attackType': 'Ranged',
        'releaseDate': '10/6/2015 12:00:00 AM'
    },
    {
        'id': '46',
        'name': 'Lúcio',
        'shortName': 'lucio',
        'alternativeName': 'Lucio',
        'nickname': '',
        'oldRole': 'Support',
        'role': 'Healer',
        'attackType': 'Ranged',
        'releaseDate': '2/14/2017 12:00:00 AM'
    },
    {
        'id': '47',
        'name': 'Lunara',
        'shortName': 'lunara',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '12/15/2015 12:00:00 AM'
    },
    {
        'id': '48',
        'name': 'Maiev',
        'shortName': 'maiev',
        'alternativeName': '',
        'oldRole': 'Assassin',
        'role': 'Melee Assassin',
        'attackType': 'Melee',
        'releaseDate': '2/6/2018 12:00:00 AM'
    },
    {
        'id': '49',
        'name': 'Mal\'Ganis',
        'shortName': 'malganis',
        'alternativeName': 'MalGanis',
        'nickname': 'malg,mal',
        'oldRole': 'Warrior',
        'role': 'Tank',
        'attackType': 'Melee',
        'releaseDate': '9/4/2018 12:00:00 AM'
    },
    {
        'id': '50',
        'name': 'Malfurion',
        'shortName': 'malfurion',
        'alternativeName': '',
        'nickname': 'malf',
        'oldRole': 'Support',
        'role': 'Healer',
        'attackType': 'Ranged',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '51',
        'name': 'Malthael',
        'shortName': 'malthael',
        'alternativeName': '',
        'nickname': 'malth',
        'oldRole': 'Assassin',
        'role': 'Bruiser',
        'attackType': 'Melee',
        'releaseDate': '6/13/2017 12:00:00 AM'
    },
    {
        'id': '52',
        'name': 'Medivh',
        'shortName': 'medivh',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Specialist',
        'role': 'Support',
        'attackType': 'Ranged',
        'releaseDate': '6/14/2016 12:00:00 AM'
    },
    {
        'id': '53',
        'name': 'Mei',
        'shortName': 'mei',
        'alternativeName': 'MeiOW',
        'nickname': '',
        'oldRole': '',
        'role': 'Bruiser',
        'attackType': 'Ranged',
        'releaseDate': '6/23/2020 12:00:00 AM'
    },
    {
        'id': '54',
        'name': 'Mephisto',
        'shortName': 'mephisto',
        'alternativeName': '',
        'nickname': 'meph',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '9/4/2018 12:00:00 AM'
    },
    {
        'id': '55',
        'name': 'Muradin',
        'shortName': 'muradin',
        'alternativeName': '',
        'nickname': 'mura',
        'oldRole': 'Warrior',
        'role': 'Tank',
        'attackType': 'Melee',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '56',
        'name': 'Murky',
        'shortName': 'murky',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Specialist',
        'role': 'Melee Assassin',
        'attackType': 'Melee',
        'releaseDate': '3/17/2015 12:00:00 AM'
    },
    {
        'id': '57',
        'name': 'Nazeebo',
        'shortName': 'nazeebo',
        'alternativeName': 'WitchDoctor',
        'nickname': 'naz',
        'oldRole': 'Specialist',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '12/2/2014 12:00:00 AM'
    },
    {
        'id': '58',
        'name': 'Nova',
        'shortName': 'nova',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '59',
        'name': 'Orphea',
        'shortName': 'orphea',
        'alternativeName': '',
        'nickname': 'orph',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '11/13/2018 12:00:00 AM'
    },
    {
        'id': '60',
        'name': 'Probius',
        'shortName': 'probius',
        'alternativeName': '',
        'nickname': 'probe,prob',
        'oldRole': 'Specialist',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '3/14/2017 12:00:00 AM'
    },
    {
        'id': '61',
        'name': 'Qhira',
        'shortName': 'qhira',
        'alternativeName': 'NexusHunter',
        'nickname': '',
        'oldRole': '',
        'role': 'Melee Assassin',
        'attackType': 'Melee',
        'releaseDate': '8/6/2019 12:00:00 AM'
    },
    {
        'id': '62',
        'name': 'Ragnaros',
        'shortName': 'ragnaros',
        'alternativeName': '',
        'nickname': 'rag',
        'oldRole': 'Assassin',
        'role': 'Bruiser',
        'attackType': 'Melee',
        'releaseDate': '12/14/2016 12:00:00 AM'
    },
    {
        'id': '63',
        'name': 'Raynor',
        'shortName': 'raynor',
        'alternativeName': '',
        'nickname': 'ray',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '64',
        'name': 'Rehgar',
        'shortName': 'rehgar',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Support',
        'role': 'Healer',
        'attackType': 'Melee',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '65',
        'name': 'Rexxar',
        'shortName': 'rexxar',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Warrior',
        'role': 'Bruiser',
        'attackType': 'Ranged',
        'releaseDate': '9/8/2015 12:00:00 AM'
    },
    {
        'id': '66',
        'name': 'Samuro',
        'shortName': 'samuro',
        'alternativeName': '',
        'nickname': 'sam',
        'oldRole': 'Assassin',
        'role': 'Melee Assassin',
        'attackType': 'Melee',
        'releaseDate': '10/18/2016 12:00:00 AM'
    },
    {
        'id': '67',
        'name': 'Sgt. Hammer',
        'shortName': 'sgthammer',
        'alternativeName': 'Sergeant Hammer',
        'nickname': 'hammer',
        'oldRole': 'Specialist',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '68',
        'name': 'Sonya',
        'shortName': 'sonya',
        'alternativeName': 'Barbarian',
        'nickname': '',
        'oldRole': 'Warrior',
        'role': 'Bruiser',
        'attackType': 'Melee',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '69',
        'name': 'Stitches',
        'shortName': 'stitches',
        'alternativeName': '',
        'nickname': 'stitch',
        'oldRole': 'Warrior',
        'role': 'Tank',
        'attackType': 'Melee',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '70',
        'name': 'Stukov',
        'shortName': 'stukov',
        'alternativeName': '',
        'nickname': 'stuk',
        'oldRole': 'Support',
        'role': 'Healer',
        'attackType': 'Ranged',
        'releaseDate': '7/11/2017 12:00:00 AM'
    },
    {
        'id': '71',
        'name': 'Sylvanas',
        'shortName': 'sylvanas',
        'alternativeName': '',
        'nickname': 'sylv',
        'oldRole': 'Specialist',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '3/10/2015 12:00:00 AM'
    },
    {
        'id': '72',
        'name': 'Tassadar',
        'shortName': 'tassadar',
        'alternativeName': '',
        'nickname': 'tass',
        'oldRole': 'Support',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '73',
        'name': 'The Butcher',
        'shortName': 'thebutcher',
        'alternativeName': 'Butcher',
        'nickname': 'butch',
        'oldRole': 'Assassin',
        'role': 'Melee Assassin',
        'attackType': 'Melee',
        'releaseDate': '6/30/2015 12:00:00 AM'
    },
    {
        'id': '74',
        'name': 'The Lost Vikings',
        'shortName': 'lostvikings',
        'alternativeName': 'LostVikings',
        'nickname': 'tlv,vikings',
        'oldRole': 'Specialist',
        'role': 'Support',
        'attackType': 'Melee',
        'releaseDate': '2/10/2015 12:00:00 AM'
    },
    {
        'id': '75',
        'name': 'Thrall',
        'shortName': 'thrall',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Assassin',
        'role': 'Bruiser',
        'attackType': 'Melee',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '76',
        'name': 'Tracer',
        'shortName': 'tracer',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '4/19/2016 12:00:00 AM'
    },
    {
        'id': '77',
        'name': 'Tychus',
        'shortName': 'tychus',
        'alternativeName': '',
        'nickname': 'tych',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '3/27/2014 12:00:00 AM'
    },
    {
        'id': '78',
        'name': 'Tyrael',
        'shortName': 'tyrael',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Warrior',
        'role': 'Tank',
        'attackType': 'Melee',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '79',
        'name': 'Tyrande',
        'shortName': 'tyrande',
        'alternativeName': '',
        'nickname': 'tyr',
        'oldRole': 'Support',
        'role': 'Healer',
        'attackType': 'Ranged',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '80',
        'name': 'Uther',
        'shortName': 'uther',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Support',
        'role': 'Healer',
        'attackType': 'Melee',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '81',
        'name': 'Valeera',
        'shortName': 'valeera',
        'alternativeName': '',
        'nickname': 'val',
        'oldRole': 'Assassin',
        'role': 'Melee Assassin',
        'attackType': 'Melee',
        'releaseDate': '1/24/2017 12:00:00 AM'
    },
    {
        'id': '82',
        'name': 'Valla',
        'shortName': 'valla',
        'nickname': '',
        'alternativeName': 'DemonHunter',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '83',
        'name': 'Varian',
        'shortName': 'varian',
        'alternativeName': '',
        'nickname': 'var',
        'oldRole': 'Multiclass',
        'role': 'Bruiser',
        'attackType': 'Melee',
        'releaseDate': '11/15/2016 12:00:00 AM'
    },
    {
        'id': '84',
        'name': 'Whitemane',
        'shortName': 'whitemane',
        'alternativeName': '',
        'nickname': 'wm',
        'oldRole': 'Support',
        'role': 'Healer',
        'attackType': 'Ranged',
        'releaseDate': '8/7/2018 12:00:00 AM'
    },
    {
        'id': '85',
        'name': 'Xul',
        'shortName': 'xul',
        'alternativeName': 'Necromancer',
        'nickname': '',
        'oldRole': 'Specialist',
        'role': 'Bruiser',
        'attackType': 'Melee',
        'releaseDate': '3/1/2016 12:00:00 AM'
    },
    {
        'id': '86',
        'name': 'Yrel',
        'shortName': 'yrel',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Warrior',
        'role': 'Bruiser',
        'attackType': 'Melee',
        'releaseDate': '6/12/2018 12:00:00 AM'
    },
    {
        'id': '87',
        'name': 'Zagara',
        'shortName': 'zagara',
        'alternativeName': '',
        'nickname': 'zag',
        'oldRole': 'Specialist',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '88',
        'name': 'Zarya',
        'shortName': 'zarya',
        'alternativeName': '',
        'nickname': '',
        'oldRole': 'Warrior',
        'role': 'Support',
        'attackType': 'Ranged',
        'releaseDate': '9/27/2016 12:00:00 AM'
    },
    {
        'id': '89',
        'name': 'Zeratul',
        'shortName': 'zeratul',
        'alternativeName': '',
        'nickname': 'zera',
        'oldRole': 'Assassin',
        'role': 'Melee Assassin',
        'attackType': 'Melee',
        'releaseDate': '3/13/2014 12:00:00 AM'
    },
    {
        'id': '90',
        'name': 'Zul\'jin',
        'shortName': 'zuljin',
        'alternativeName': 'Zuljin',
        'nickname': 'zj',
        'oldRole': 'Assassin',
        'role': 'Ranged Assassin',
        'attackType': 'Ranged',
        'releaseDate': '1/4/2017 12:00:00 AM'
    }
]

talent_tiers = ["1", "4", "7", "10", "13", "16", "20"]

altname_to_shortname = {hero['alternativeName']: hero['shortName'] for hero in hero_data}


def wald_interval(x, n, confidence=0.95):

    if x >= 1 and n >= 1:
        p = x / n
        # todo this is slightly more accurate, but requires importing scipy.stats. Increase accuracy later
        # z = stats.norm.ppf(1 - (1 - confidence) / 2)
        z = math.sqrt(2) * erfinv(confidence)
        se = math.sqrt(p * (1 - p) / n)
        me = z * se
        return me
    return 0


def erfinv(y):
    a = 0.147
    sign = 1 if y >= 0 else -1
    ln_term = math.log(1 - y**2)
    term = 2 / (math.pi * a) + ln_term / 2
    term2 = ln_term / a
    return sign * math.sqrt(math.sqrt(term**2 - term2) - term)


def clean_string(val: str, remove_spaces=True):
    """
    :param val: any string
    :param remove_spaces: optional parameter on whether to also remove any spaces in the string
    :return: the same string in lower case, without punctuation, and without special characters
    """
    if remove_spaces:
        return unidecode(val.lower()).translate(val.maketrans('', '', string.punctuation)).replace(" ", "")
    return unidecode(val.lower()).translate(val.maketrans('', '', string.punctuation))


def clean_entity_name(val: str):
    """
    slight work around to heroes-talents using "lostvikings" instead of "thelostvikings", and "chogall" instead of "cho"
    """
    name = clean_string(val)

    replacements = {
        "thelostvikings": "lostvikings",
        "cho": "chogall",
        "braxisoutpost": "braxisholdout"
    }

    return replacements.get(name, name)


def load_partial_json(path, max_entries=2000, start_position=0):
    sorted_data = SortedDict(lambda x: -x)
    end_position = start_position

    try:
        with open(path, 'r') as f:
            f.seek(start_position)
            parser = ijson.items(f, '')
            entry_count = 0

            for entry in parser:
                end_position = f.tell()
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

    ret = {
        'sorted_data': sorted_data,
        'end_position': end_position
    }

    return ret


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


def get_hero_by_id(hero_id: int):
    """
    :param hero_id: integer
    :return: string of the hero name, or "" if out of bounds
    """
    try:
        return hero_ids[hero_id]
    except KeyError:
        return ""


def get_id_by_hero(hero_name: string, check_alt_names=False):
    """
    :param hero_name: string
    :return: int, -1 if invalid hero name
    """
    try:
        return list(hero_ids.keys())[list(hero_ids.values()).index(clean_string(hero_name))]
    except ValueError:
        if check_alt_names:
            return list()
        return -1

def get_shortname_by_altname(alt_name: string):
    """

    :param alt_name:
    :return: the hero's shortname given their altname
    """

    try:
        return altname_to_shortname[alt_name]
    except KeyError:
        return clean_string(alt_name)


def update_player_tables(match_data):
    player_data = None
    file = None

    try:
        file = open("player-data.json")
    except FileNotFoundError:
        print("player-data.json not found. Creating it")
        with open("player-data.json", "w") as f:
            json.dump(player_data, f, indent=4)
        file = open("player-data.json")

    player_data = json.load(file)


def create_empty_hero_table(create_json=False):
    hero_table = copy.deepcopy(hero_data)

    for hero in hero_table:
        hero['gamesPlayed'] = 0
        hero['gamesWon'] = 0
        hero['gamesBanned'] = 0
        hero['totalDamage'] = 0
        hero['totalHealing'] = 0
        hero['totalDamageSoaked'] = 0
        hero['totalExperience'] = 0
        hero['totalSiege'] = 0
        hero['talentGames'] = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0],
                               [0, 0, 0, 0, 0]]
        hero['talentWins'] = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0],
                              [0, 0, 0, 0, 0]]
        # currently doing this based on levels, maybe better to brute force?
        hero['talentNormalizedGames'] = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0],
                                         [0, 0, 0, 0], [0, 0, 0, 0, 0]]
        hero['talentNormalizedWins'] = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0],
                                        [0, 0, 0, 0], [0, 0, 0, 0, 0]]
        hero['allyHeroGames'] = [0] * 90
        hero['allyHeroWins'] = [0] * 90
        hero['enemyHeroGames'] = [0] * 90
        hero['enemyHeroWins'] = [0] * 90

    if create_json:
        with open('hero_table.json', 'w') as f:
            json.dump(hero_table, f)

    return hero_table

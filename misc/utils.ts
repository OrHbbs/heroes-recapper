//included this just for reference, don't use

export interface StormReplay {
    "match": {
        "version": {
            "m_flags": number,
            "m_major": number,
            "m_minor": number,
            "m_revision": number,
            "m_build": number,
            "m_baseBuild": number
        },
        "type": number,
        "loopLength": number,
        "filename": `${string}.StormReplay`,
        "mode": number,
        "map": string,
        "date": number,
        "rawDate": number,
        "playerIDs": `1-Hero-1-${number}`[],
        "heroes": string[],
        "levelTimes": {
            [key: string]: {
                loop: number,
                level: number,
                team: string,
                time: number
            }[]
        }
        "region": number,
        "bans": {
            "0": {
                "hero": string,
                "order": number,
                "absolute": number
            }[],
            "1": {
                "hero": string,
                "order": number,
                "absolute": number
            }[]
        },
        "picks": {
            "0": string[5],
            "1": string[5],
            "first": 0
        },
        "levelAdvTimeline": {
            "start": number,
            "end": number,
            "levelDiff": number,
            "length": number
        }[],
        "firstPickWin": boolean,
        "firstObjective": number,
        "firstObjectiveWin": boolean,
        "firstFort": number,
        "firstKeep": number,
        "firstFortWin": boolean,
        "firstKeepWin": boolean
    }
    "players": {
        [key: string]: {
            "hero": string, //todo this should be 1 of 90 values
            "name": string,
            "team": 0 | 1,
            "gameStats": {
                "awards": [],
                "Takedowns": number,
                "Deaths": number,
                /** todo what is this */
                "TownKills": number,
                /** aka last hit */
                "SoloKill": number,
                "Assists": number,
                "Level": number,
                /** todo what is this */
                "TeamTakedowns": number,
                "ExperienceContribution": number,
                /** healing to allies only */
                "Healing": number,
                "SiegeDamage": number,
                "StructureDamage": number,
                "MinionDamage": number,
                "HeroDamage": number,
                "MercCampCaptures": number,
                "SelfHealing": number,
                "TimeSpentDead": number,
                "TimeCCdEnemyHeroes": number,
                /** todo what is this */
                "CreepDamage": number,
                "SummonDamage": number,
                "Tier1Talent": number,
                "Tier2Talent": number,
                "Tier3Talent": number,
                "Tier4Talent": number,
                "Tier5Talent": number,
                "Tier6Talent": number,
                "Tier7Talent": number,
                "DamageTaken": number,
                /** todo what is the difference between this and DamageTaken */
                "DamageSoaked": number,
                "HighestKillStreak": number,
                "ProtectionGivenToAllies": number,
                "TimeSilencingEnemyHeroes": number,
                "TimeRootingEnemyHeroes": number,
                "TimeStunningEnemyHeroes": number,
                "ClutchHealsPerformed": number,
                "EscapesPerformed": number,
                "VengeancesPerformed": number,
                "TeamfightEscapesPerformed": number,
                "OutnumberedDeaths": number,
                "TeamfightHealingDone": number,
                "TeamfightDamageTaken": number,
                "TeamfightHeroDamage": number,
                "OnFireTimeOnFire": number,
                "TimeOnPoint": number,
                /** alterac pass specific */
                "CageUnlocksInterrupted": number
                "PhysicalDamage": number,
                "SpellDamage": number,
                "Multikill": number,
                "MinionKills": number,
                "RegenGlobes": number,
                /**sky temple specific*/
                "TimeInTemple": number,
                "KDA": number,
                "aces": number,
                "wipes": number,
            },
            "deaths": {
                "loop": number,
                "time": number,
                "x": number,
                "y": number,
                "killers": {
                        player: string,
                        hero: string
                }[],
            }[],
        }[]
    },
    /** This should be 1. If it's not, it's not a valid replay*/
    "status": number
}

export interface HeroData {
    id: `${number}`;
    name: string;
    shortName: string;
    alternativeName: string;
    nickname?: string[]
    oldRole: "Assassin" | "Multiclass" | "Specialist" | "Support" | "Warrior" | "";
    role: "Tank" | "Bruiser" | "Ranged Assassin" | "Melee Assassin" | "Healer" | "Support";
    attackType: "Melee" | "Ranged";
    releaseDate: string;
    // gamesPlayed: number;
}

export const heroes: HeroData[] = [
    {
        id: '1',
        name: 'Abathur',
        shortName: 'abathur',
        alternativeName: '',
        nickname: ['aba'],
        oldRole: 'Specialist',
        role: 'Support',
        attackType: 'Melee',
        releaseDate: '3/13/2014 12:00:00 AM',
        // gamesPlayed: 0
    },
    {
        id: '2',
        name: 'Alarak',
        shortName: 'alarak',
        alternativeName: '',
        nickname: [],
        oldRole: 'Assassin',
        role: 'Melee Assassin',
        attackType: 'Melee',
        releaseDate: '9/13/2016 12:00:00 AM'
    },
    {
        id: '3',
        name: 'Alexstrasza',
        shortName: 'alexstrasza',
        alternativeName: '',
        nickname: ['alex'],
        oldRole: 'Support',
        role: 'Healer',
        attackType: 'Ranged',
        releaseDate: '11/14/2017 12:00:00 AM'
    },
    {
        id: '4',
        name: 'Ana',
        shortName: 'ana',
        alternativeName: '',
        nickname: [],
        oldRole: 'Support',
        role: 'Healer',
        attackType: 'Ranged',
        releaseDate: '9/26/2017 12:00:00 AM'
    },
    {
        id: '5',
        name: 'Anduin',
        shortName: 'anduin',
        alternativeName: '',
        oldRole: '',
        nickname: [],
        role: 'Healer',
        attackType: 'Ranged',
        releaseDate: '6/18/2019 12:00:00 AM'
    },
    {
        id: '6',
        name: 'Anub\'arak',
        shortName: 'anubarak',
        alternativeName: 'Anubarak',
        nickname: ['anub'],
        oldRole: 'Warrior',
        role: 'Tank',
        attackType: 'Melee',
        releaseDate: '3/18/2014 12:00:00 AM'
    },
    {
        id: '7',
        name: 'Artanis',
        shortName: 'artanis',
        alternativeName: '',
        nickname: ['art'],
        oldRole: 'Warrior',
        role: 'Bruiser',
        attackType: 'Melee',
        releaseDate: '10/20/2015 12:00:00 AM'
    },
    {
        id: '8',
        name: 'Arthas',
        shortName: 'arthas',
        alternativeName: '',
        nickname: [],
        oldRole: 'Warrior',
        role: 'Tank',
        attackType: 'Melee',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '9',
        name: 'Auriel',
        shortName: 'auriel',
        alternativeName: '',
        nickname: [],
        oldRole: 'Support',
        role: 'Healer',
        attackType: 'Ranged',
        releaseDate: '6/14/2016 12:00:00 AM'
    },
    {
        id: '10',
        name: 'Azmodan',
        shortName: 'azmodan',
        alternativeName: '',
        nickname: ['azmo'],
        oldRole: 'Specialist',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '11',
        name: 'Blaze',
        shortName: 'blaze',
        alternativeName: 'Firebat',
        nickname: [],
        oldRole: 'Warrior',
        role: 'Tank',
        attackType: 'Ranged',
        releaseDate: '1/9/2018 12:00:00 AM'
    },
    {
        id: '12',
        name: 'Brightwing',
        shortName: 'brightwing',
        alternativeName: 'FaerieDragon',
        nickname: ['bw'],
        oldRole: 'Support',
        role: 'Healer',
        attackType: 'Ranged',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '13',
        name: 'Cassia',
        shortName: 'cassia',
        alternativeName: 'Amazon',
        nickname: [],
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '4/4/2017 12:00:00 AM'
    },
    {
        id: '14',
        name: 'Chen',
        shortName: 'chen',
        alternativeName: '',
        nickname: [],
        oldRole: 'Warrior',
        role: 'Bruiser',
        attackType: 'Melee',
        releaseDate: '4/7/2014 12:00:00 AM'
    },
    {
        id: '15',
        name: 'Cho',
        shortName: 'cho',
        alternativeName: '',
        nickname: ['cg'],
        oldRole: 'Warrior',
        role: 'Tank',
        attackType: 'Melee',
        releaseDate: '11/17/2015 12:00:00 AM'
    },
    {
        id: '16',
        name: 'Chromie',
        shortName: 'chromie',
        alternativeName: '',
        nickname: [],
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '5/17/2016 12:00:00 AM'
    },
    {
        id: '17',
        name: 'Deathwing',
        shortName: 'deathwing',
        alternativeName: '',
        nickname: ['dw'],
        oldRole: '',
        role: 'Bruiser',
        attackType: 'Melee',
        releaseDate: '11/12/2019 12:00:00 AM'
    },
    {
        id: '18',
        name: 'Deckard',
        shortName: 'deckard',
        alternativeName: '',
        nickname: ['old man'],
        oldRole: 'Support',
        role: 'Healer',
        attackType: 'Ranged',
        releaseDate: '4/24/2018 12:00:00 AM'
    },
    {
        id: '19',
        name: 'Dehaka',
        shortName: 'dehaka',
        alternativeName: '',
        nickname: ['dino'],
        oldRole: 'Warrior',
        role: 'Bruiser',
        attackType: 'Melee',
        releaseDate: '3/29/2016 12:00:00 AM'
    },
    {
        id: '20',
        name: 'Diablo',
        shortName: 'diablo',
        alternativeName: '',
        nickname: ['dibbles'],
        oldRole: 'Warrior',
        role: 'Tank',
        attackType: 'Melee',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '21',
        name: 'D.Va',
        shortName: 'dva',
        alternativeName: '',
        nickname: [],
        oldRole: 'Warrior',
        role: 'Tank',
        attackType: 'Ranged',
        releaseDate: '5/16/2017 12:00:00 AM'
    },
    {
        id: '22',
        name: 'E.T.C.',
        shortName: 'etc',
        alternativeName: 'L90ETC',
        nickname: ['cow'],
        oldRole: 'Warrior',
        role: 'Tank',
        attackType: 'Melee',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '23',
        name: 'Falstad',
        shortName: 'falstad',
        alternativeName: '',
        nickname: ['fals', 'chicken'],
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '24',
        name: 'Fenix',
        shortName: 'fenix',
        alternativeName: '',
        nickname: [],
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '4/24/2018 12:00:00 AM'
    },
    {
        id: '25',
        name: 'Gall',
        shortName: 'gall',
        nickname: ['cg'],
        alternativeName: '',
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '11/17/2015 12:00:00 AM'
    },
    {
        id: '26',
        name: 'Garrosh',
        shortName: 'garrosh',
        alternativeName: '',
        nickname: ['garry'],
        oldRole: 'Warrior',
        role: 'Tank',
        attackType: 'Melee',
        releaseDate: '8/8/2017 12:00:00 AM'
    },
    {
        id: '27',
        name: 'Gazlowe',
        shortName: 'gazlowe',
        alternativeName: 'Tinker',
        nickname: ['gaz'],
        oldRole: 'Specialist',
        role: 'Bruiser',
        attackType: 'Melee',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '28',
        name: 'Genji',
        shortName: 'genji',
        alternativeName: '',
        nickname: [],
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '4/25/2017 12:00:00 AM'
    },
    {
        id: '29',
        name: 'Greymane',
        shortName: 'greymane',
        alternativeName: '',
        nickname: ['grey', 'gm'],
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '1/12/2016 12:00:00 AM'
    },
    {
        id: '30',
        name: 'Gul\'dan',
        shortName: 'guldan',
        alternativeName: 'Guldan',
        nickname: [],
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '8/2/2016 12:00:00 AM'
    },
    {
        id: '31',
        name: 'Hanzo',
        shortName: 'hanzo',
        alternativeName: '',
        nickname: [],
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '12/12/2017 12:00:00 AM'
    },
    {
        id: '32',
        name: 'Hogger',
        shortName: 'hogger',
        alternativeName: '',
        nickname: ['hog'],
        oldRole: '',
        role: 'Bruiser',
        attackType: 'Melee',
        releaseDate: '12/1/2020 12:00:00 AM'
    },
    {
        id: '33',
        name: 'Illidan',
        shortName: 'illidan',
        alternativeName: '',
        nickname: ['illi'],
        oldRole: 'Assassin',
        role: 'Melee Assassin',
        attackType: 'Melee',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '34',
        name: 'Imperius',
        shortName: 'imperius',
        alternativeName: '',
        nickname: ['imp'],
        oldRole: 'Warrior',
        role: 'Bruiser',
        attackType: 'Melee',
        releaseDate: '1/8/2019 12:00:00 AM'
    },
    {
        id: '35',
        name: 'Jaina',
        shortName: 'jaina',
        alternativeName: '',
        nickname: [],
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '12/2/2014 12:00:00 AM'
    },
    {
        id: '36',
        name: 'Johanna',
        shortName: 'johanna',
        alternativeName: 'Crusader',
        nickname: ['joh', 'jo'],
        oldRole: 'Warrior',
        role: 'Tank',
        attackType: 'Melee',
        releaseDate: '6/2/2015 12:00:00 AM'
    },
    {
        id: '37',
        name: 'Junkrat',
        shortName: 'junkrat',
        alternativeName: '',
        nickname: ['junk', 'rat'],
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '10/17/2017 12:00:00 AM'
    },
    {
        id: '38',
        name: 'Kael\'thas',
        shortName: 'kaelthas',
        alternativeName: 'Kaelthas',
        nickname: ['kael', 'kt'],
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '5/12/2015 12:00:00 AM'
    },
    {
        id: '39',
        name: 'Kel\'thuzad',
        shortName: 'kelthuzad',
        alternativeName: 'Kelthuzad',
        nickname: ['ktz'],
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '10/24/2017 12:00:00 AM'
    },
    {
        id: '40',
        name: 'Kerrigan',
        shortName: 'kerrigan',
        alternativeName: '',
        nickname: ['kerri'],
        oldRole: 'Assassin',
        role: 'Melee Assassin',
        attackType: 'Melee',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '41',
        name: 'Kharazim',
        shortName: 'kharazim',
        alternativeName: 'Monk',
        nickname: ['khara', 'monk'],
        oldRole: 'Support',
        role: 'Healer',
        attackType: 'Melee',
        releaseDate: '8/18/2015 12:00:00 AM'
    },
    {
        id: '42',
        name: 'Leoric',
        shortName: 'leoric',
        alternativeName: '',
        nickname: ['leo'],
        oldRole: 'Warrior',
        role: 'Bruiser',
        attackType: 'Melee',
        releaseDate: '7/21/2015 12:00:00 AM'
    },
    {
        id: '43',
        name: 'Li Li',
        shortName: 'lili',
        alternativeName: 'LiLi',
        nickname: [],
        oldRole: 'Support',
        role: 'Healer',
        attackType: 'Ranged',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '44',
        name: 'Li-Ming',
        shortName: 'liming',
        alternativeName: 'Wizard',
        nickname: ['ming'],
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '2/2/2016 12:00:00 AM'
    },
    {
        id: '45',
        name: 'Lt. Morales',
        shortName: 'ltmorales',
        alternativeName: 'Medic',
        nickname: ['medic'],
        oldRole: 'Support',
        role: 'Healer',
        attackType: 'Ranged',
        releaseDate: '10/6/2015 12:00:00 AM'
    },
    {
        id: '46',
        name: 'Lúcio',
        shortName: 'lucio',
        alternativeName: 'Lucio',
        nickname: [],
        oldRole: 'Support',
        role: 'Healer',
        attackType: 'Ranged',
        releaseDate: '2/14/2017 12:00:00 AM'
    },
    {
        id: '47',
        name: 'Lunara',
        shortName: 'lunara',
        alternativeName: '',
        nickname: [],
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '12/15/2015 12:00:00 AM'
    },
    {
        id: '48',
        name: 'Maiev',
        shortName: 'maiev',
        alternativeName: '',
        oldRole: 'Assassin',
        role: 'Melee Assassin',
        attackType: 'Melee',
        releaseDate: '2/6/2018 12:00:00 AM'
    },
    {
        id: '49',
        name: 'Mal\'Ganis',
        shortName: 'malganis',
        alternativeName: 'MalGanis',
        nickname: ['malg', 'mal'],
        oldRole: 'Warrior',
        role: 'Tank',
        attackType: 'Melee',
        releaseDate: '9/4/2018 12:00:00 AM'
    },
    {
        id: '50',
        name: 'Malfurion',
        shortName: 'malfurion',
        alternativeName: '',
        nickname: ['malf'],
        oldRole: 'Support',
        role: 'Healer',
        attackType: 'Ranged',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '51',
        name: 'Malthael',
        shortName: 'malthael',
        alternativeName: '',
        nickname: ['malth'],
        oldRole: 'Assassin',
        role: 'Bruiser',
        attackType: 'Melee',
        releaseDate: '6/13/2017 12:00:00 AM'
    },
    {
        id: '52',
        name: 'Medivh',
        shortName: 'medivh',
        alternativeName: '',
        nickname: [],
        oldRole: 'Specialist',
        role: 'Support',
        attackType: 'Ranged',
        releaseDate: '6/14/2016 12:00:00 AM'
    },
    {
        id: '53',
        name: 'Mei',
        shortName: 'mei',
        alternativeName: 'MeiOW',
        nickname: [],
        oldRole: '',
        role: 'Bruiser',
        attackType: 'Ranged',
        releaseDate: '6/23/2020 12:00:00 AM'
    },
    {
        id: '54',
        name: 'Mephisto',
        shortName: 'mephisto',
        alternativeName: '',
        nickname: ['meph'],
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '9/4/2018 12:00:00 AM'
    },
    {
        id: '55',
        name: 'Muradin',
        shortName: 'muradin',
        alternativeName: '',
        nickname: ['mura'],
        oldRole: 'Warrior',
        role: 'Tank',
        attackType: 'Melee',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '56',
        name: 'Murky',
        shortName: 'murky',
        alternativeName: '',
        nickname: [],
        oldRole: 'Specialist',
        role: 'Melee Assassin',
        attackType: 'Melee',
        releaseDate: '3/17/2015 12:00:00 AM'
    },
    {
        id: '57',
        name: 'Nazeebo',
        shortName: 'nazeebo',
        alternativeName: 'WitchDoctor',
        nickname: ['naz'],
        oldRole: 'Specialist',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '12/2/2014 12:00:00 AM'
    },
    {
        id: '58',
        name: 'Nova',
        shortName: 'nova',
        alternativeName: '',
        nickname: [],
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '59',
        name: 'Orphea',
        shortName: 'orphea',
        alternativeName: '',
        nickname: ['orph'],
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '11/13/2018 12:00:00 AM'
    },
    {
        id: '60',
        name: 'Probius',
        shortName: 'probius',
        alternativeName: '',
        nickname: ['probe', 'prob'],
        oldRole: 'Specialist',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '3/14/2017 12:00:00 AM'
    },
    {
        id: '61',
        name: 'Qhira',
        shortName: 'qhira',
        alternativeName: 'NexusHunter',
        nickname: [],
        oldRole: '',
        role: 'Melee Assassin',
        attackType: 'Melee',
        releaseDate: '8/6/2019 12:00:00 AM'
    },
    {
        id: '62',
        name: 'Ragnaros',
        shortName: 'ragnaros',
        alternativeName: '',
        nickname: ['rag'],
        oldRole: 'Assassin',
        role: 'Bruiser',
        attackType: 'Melee',
        releaseDate: '12/14/2016 12:00:00 AM'
    },
    {
        id: '63',
        name: 'Raynor',
        shortName: 'raynor',
        alternativeName: '',
        nickname: ['ray'],
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '64',
        name: 'Rehgar',
        shortName: 'rehgar',
        alternativeName: '',
        nickname: [],
        oldRole: 'Support',
        role: 'Healer',
        attackType: 'Melee',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '65',
        name: 'Rexxar',
        shortName: 'rexxar',
        alternativeName: '',
        nickname: [],
        oldRole: 'Warrior',
        role: 'Bruiser',
        attackType: 'Ranged',
        releaseDate: '9/8/2015 12:00:00 AM'
    },
    {
        id: '66',
        name: 'Samuro',
        shortName: 'samuro',
        alternativeName: '',
        nickname: ['sam'],
        oldRole: 'Assassin',
        role: 'Melee Assassin',
        attackType: 'Melee',
        releaseDate: '10/18/2016 12:00:00 AM'
    },
    {
        id: '67',
        name: 'Sgt. Hammer',
        shortName: 'sgthammer',
        alternativeName: 'Sergeant Hammer',
        nickname: ['hammer'],
        oldRole: 'Specialist',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '68',
        name: 'Sonya',
        shortName: 'sonya',
        alternativeName: 'Barbarian',
        nickname: [],
        oldRole: 'Warrior',
        role: 'Bruiser',
        attackType: 'Melee',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '69',
        name: 'Stitches',
        shortName: 'stitches',
        alternativeName: '',
        nickname: ['stitch'],
        oldRole: 'Warrior',
        role: 'Tank',
        attackType: 'Melee',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '70',
        name: 'Stukov',
        shortName: 'stukov',
        alternativeName: '',
        nickname: ['stuk'],
        oldRole: 'Support',
        role: 'Healer',
        attackType: 'Ranged',
        releaseDate: '7/11/2017 12:00:00 AM'
    },
    {
        id: '71',
        name: 'Sylvanas',
        shortName: 'sylvanas',
        alternativeName: '',
        nickname: ['sylv'],
        oldRole: 'Specialist',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '3/10/2015 12:00:00 AM'
    },
    {
        id: '72',
        name: 'Tassadar',
        shortName: 'tassadar',
        alternativeName: '',
        nickname: ['tass'],
        oldRole: 'Support',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '73',
        name: 'The Butcher',
        shortName: 'thebutcher',
        alternativeName: 'Butcher',
        nickname: ['butch'],
        oldRole: 'Assassin',
        role: 'Melee Assassin',
        attackType: 'Melee',
        releaseDate: '6/30/2015 12:00:00 AM'
    },
    {
        id: '74',
        name: 'The Lost Vikings',
        shortName: 'lostvikings',
        alternativeName: 'LostVikings',
        nickname: ['tlv', 'vikings'],
        oldRole: 'Specialist',
        role: 'Support',
        attackType: 'Melee',
        releaseDate: '2/10/2015 12:00:00 AM'
    },
    {
        id: '75',
        name: 'Thrall',
        shortName: 'thrall',
        alternativeName: '',
        nickname: [],
        oldRole: 'Assassin',
        role: 'Bruiser',
        attackType: 'Melee',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '76',
        name: 'Tracer',
        shortName: 'tracer',
        alternativeName: '',
        nickname: [],
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '4/19/2016 12:00:00 AM'
    },
    {
        id: '77',
        name: 'Tychus',
        shortName: 'tychus',
        alternativeName: '',
        nickname: ['tych'],
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '3/27/2014 12:00:00 AM'
    },
    {
        id: '78',
        name: 'Tyrael',
        shortName: 'tyrael',
        alternativeName: '',
        nickname: [],
        oldRole: 'Warrior',
        role: 'Tank',
        attackType: 'Melee',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '79',
        name: 'Tyrande',
        shortName: 'tyrande',
        alternativeName: '',
        nickname: ['tyr'],
        oldRole: 'Support',
        role: 'Healer',
        attackType: 'Ranged',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '80',
        name: 'Uther',
        shortName: 'uther',
        alternativeName: '',
        nickname: [],
        oldRole: 'Support',
        role: 'Healer',
        attackType: 'Melee',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '81',
        name: 'Valeera',
        shortName: 'valeera',
        alternativeName: '',
        nickname: ['val'],
        oldRole: 'Assassin',
        role: 'Melee Assassin',
        attackType: 'Melee',
        releaseDate: '1/24/2017 12:00:00 AM'
    },
    {
        id: '82',
        name: 'Valla',
        shortName: 'valla',
        nickname: [],
        alternativeName: 'DemonHunter',
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '83',
        name: 'Varian',
        shortName: 'varian',
        alternativeName: '',
        nickname: ['var'],
        oldRole: 'Multiclass',
        role: 'Bruiser',
        attackType: 'Melee',
        releaseDate: '11/15/2016 12:00:00 AM'
    },
    {
        id: '84',
        name: 'Whitemane',
        shortName: 'whitemane',
        alternativeName: '',
        nickname: ['wm'],
        oldRole: 'Support',
        role: 'Healer',
        attackType: 'Ranged',
        releaseDate: '8/7/2018 12:00:00 AM'
    },
    {
        id: '85',
        name: 'Xul',
        shortName: 'xul',
        alternativeName: 'Necromancer',
        nickname: [],
        oldRole: 'Specialist',
        role: 'Bruiser',
        attackType: 'Melee',
        releaseDate: '3/1/2016 12:00:00 AM'
    },
    {
        id: '86',
        name: 'Yrel',
        shortName: 'yrel',
        alternativeName: '',
        nickname: [],
        oldRole: 'Warrior',
        role: 'Bruiser',
        attackType: 'Melee',
        releaseDate: '6/12/2018 12:00:00 AM'
    },
    {
        id: '87',
        name: 'Zagara',
        shortName: 'zagara',
        alternativeName: '',
        nickname: ['zag'],
        oldRole: 'Specialist',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '88',
        name: 'Zarya',
        shortName: 'zarya',
        alternativeName: '',
        nickname: [],
        oldRole: 'Warrior',
        role: 'Support',
        attackType: 'Ranged',
        releaseDate: '9/27/2016 12:00:00 AM'
    },
    {
        id: '89',
        name: 'Zeratul',
        shortName: 'zeratul',
        alternativeName: '',
        nickname: ['zera'],
        oldRole: 'Assassin',
        role: 'Melee Assassin',
        attackType: 'Melee',
        releaseDate: '3/13/2014 12:00:00 AM'
    },
    {
        id: '90',
        name: 'Zul\'jin',
        shortName: 'zuljin',
        alternativeName: 'Zuljin',
        nickname: ['zj'],
        oldRole: 'Assassin',
        role: 'Ranged Assassin',
        attackType: 'Ranged',
        releaseDate: '1/4/2017 12:00:00 AM'
    }
];

export interface PlayerData {
    games: number,
    aliases: string[],

}

export const playerData: PlayerData = {
    games: 0,
    aliases: [],

}
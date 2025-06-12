import re
import struct
from io import BytesIO
from collections import defaultdict

import mpyq

class BitReader:
    def __init__(self, stream):
        self.stream = stream
        self.bit_buffer = 0
        self.bit_count = 0

    def read(self, num_bits):
        result = 0
        bits_to_read = num_bits
        while bits_to_read > 0:
            if self.bit_count == 0:
                self.bit_buffer = ord(self.stream.read(1))
                self.bit_count = 8
            take_bits = min(bits_to_read, self.bit_count)
            result = (result << take_bits) | (self.bit_buffer >> (self.bit_count - take_bits)) & ((1 << take_bits) - 1)
            self.bit_count -= take_bits
            bits_to_read -= take_bits
        return result

    def read_bytes(self, num_bytes):
        return self.stream.read(num_bytes)

    def align_to_byte(self):
        self.bit_count = 0

    def read_string(self, length):
        try:
            return self.stream.read(length).decode('utf-8', errors='ignore')  # Use errors='ignore' to skip invalid bytes
        except UnicodeDecodeError:
            return ''

    def read_int16(self):
        return struct.unpack('h', self.stream.read(2))[0]

    def read_int32(self):
        return struct.unpack('i', self.stream.read(4))[0]

    def read_int64(self):
        return struct.unpack('q', self.stream.read(8))[0]

    def read_blob_preceded_with_length(self, length_bits):
        length = self.read(length_bits)
        return self.read_bytes(length)


def parse_replay(replay, buffer):
    stream = BytesIO(buffer)
    bit_reader = BitReader(stream)

    # Condition for handling different versions
    if replay['ReplayBuild'] < 47479 or replay['ReplayBuild'] < 47903 or replay['ReplayBuild'] in [52124, 52381] or replay['GameMode'] == 'Unknown':
        get_battle_tags(replay, bit_reader)
        return

    # Reading dependencies
    dependencies_length = bit_reader.read(6)
    print(f"Dependencies length: {dependencies_length}")
    for _ in range(dependencies_length):
        # Read the dependency blob (preceded with length)
        dependency = bit_reader.read_blob_preceded_with_length(10)
        print(f"Dependency: {dependency}")

    # Reading s2ma cache handles
    s2ma_cache_handles_length = bit_reader.read(6)
    print(f"s2ma cache handles length: {s2ma_cache_handles_length}")

    for _ in range(s2ma_cache_handles_length):
        bit_reader.align_to_byte()  # Align to the byte boundary
        s2ma_marker = bit_reader.read_string(8)  # Read the s2ma marker
        print(f"s2ma marker: {s2ma_marker}")

        # if s2ma_marker != "s2ma":
        #     raise Exception("Expected 's2ma' cache handle, but got something else!")

        # Read the 36 bytes after 's2ma'
        bit_reader.read_bytes(36)

    # Proceed to the detailed parsing step
    detailed_parse(bit_reader, replay, s2ma_cache_handles_length)


def detailed_parse(bit_reader, replay, s2ma_cache_handles_length):
    bit_reader.align_to_byte()

    while True:
        if bit_reader.read_string(4) == "s2mh":
            bit_reader.stream.seek(bit_reader.stream.tell() - 4)
            break
        else:
            bit_reader.stream.seek(bit_reader.stream.tell() - 3)

    for _ in range(s2ma_cache_handles_length):
        bit_reader.align_to_byte()
        if bit_reader.read_string(4) != "s2mh":
            raise Exception("s2mh cache")
        bit_reader.read_bytes(36)

    player_collection = []
    if replay['ReplayBuild'] >= 48027:
        collection_size = bit_reader.read_int16()
    else:
        collection_size = bit_reader.read_int32()

    if collection_size > 8000:
        raise Exception("collectionSize is an unusually large number")

    for _ in range(collection_size):
        if replay['ReplayBuild'] >= 55929:
            bit_reader.read_bytes(8)
        else:
            player_collection.append(bit_reader.read_string(bit_reader.read(8)))

    if bit_reader.read_int32() != collection_size:
        raise Exception("skinArrayLength not equal")

    for _ in range(collection_size):
        for j in range(16):  # assuming 16 player slots
            bit_reader.read(8)
            num = bit_reader.read(8)

            if replay['ReplayBuild'] < 55929:
                client = replay['ClientListByUserID'].get(j)
                if client:
                    if num > 0:
                        client['PlayerCollectionDictionary'][player_collection[i]] = True
                    elif num == 0:
                        client['PlayerCollectionDictionary'][player_collection[i]] = False
                    else:
                        raise NotImplementedError()

    if replay['ReplayBuild'] >= 85027:
        disabled_hero_list_length = bit_reader.read(8)
        for _ in range(disabled_hero_list_length):
            disabled_hero_attribute_id = bit_reader.read_string(32)
            replay['DisabledHeroes'].append(disabled_hero_attribute_id)

    # Player info
    if replay.get('RandomValue', 0) == 0:
        replay['RandomValue'] = bit_reader.read_int32()
    else:
        bit_reader.read_int32()

    bit_reader.read_bytes(4)

    player_list_length = bit_reader.read(5)
    for i in range(player_list_length):
        bit_reader.read(32)
        bit_reader.read(5)
        bit_reader.read(8)  # m_region
        if bit_reader.read_string(32) != "Hero":
            raise Exception("Not Hero")
        bit_reader.read(32)
        bit_reader.read_int64()
        bit_reader.read(8)
        if bit_reader.read_string(32) != "Hero":
            raise Exception("Not Hero")
        bit_reader.read(32)

        id_length = bit_reader.read(7) + 2
        bit_reader.align_to_byte()
        replay['ClientListByUserID'][i]['BattleNetTId'] = bit_reader.read_string(id_length)

        bit_reader.read(6)

        if replay['ReplayBuild'] <= 47479:
            bit_reader.read(8)
            if bit_reader.read_string(32) != "Hero":
                raise Exception("Not Hero")
            bit_reader.read(32)
            id_length = bit_reader.read(7) + 2
            bit_reader.align_to_byte()
            if replay['ClientListByUserID'][i]['BattleNetTId'] != bit_reader.read_string(id_length):
                raise Exception("Duplicate internal id does not match")

        bit_reader.read(2)
        bit_reader.read_bytes(25)
        bit_reader.read(24)

        if replay['GameMode'] == 'Cooperative':
            bit_reader.read_bytes(8)

        bit_reader.read(7)

        if not bit_reader.read(1):
            if replay['ReplayBuild'] >= 51609 or replay['ReplayBuild'] in [47903, 47479]:
                bit_reader.read_bytes(bit_reader.read(12))
            elif replay['ReplayBuild'] > 47219:
                bit_reader.read_bytes(bit_reader.read(15) * 2)
            else:
                bit_reader.read_bytes(bit_reader.read(9))

        bit_reader.read(1)

        if bit_reader.read(1):
            replay['ClientListByUserID'][i]['PartyValue'] = bit_reader.read_int32() + bit_reader.read_int32()

        bit_reader.read(1)
        battle_tag = bit_reader.read_blob_preceded_with_length(7).decode('utf-8').split('#')
        if battle_tag[0] != replay['ClientListByUserID'][i]['Name']:
            raise Exception("Couldn't find BattleTag")
        if len(battle_tag) == 2:
            replay['ClientListByUserID'][i]['BattleTag'] = int(battle_tag[1])

        if replay['ReplayBuild'] >= 52860:
            replay['ClientListByUserID'][i]['AccountLevel'] = bit_reader.read_int32()

        if replay['ReplayBuild'] >= 69947:
            bit_reader.read(1)


def get_battle_tags(replay, bit_reader):
    pass


def group_players(players_data):
    solo_players = []
    party_groups = defaultdict(list)

    for player in players_data:
        # Check if the 8-byte sequence starts with b'\x00@'
        # print(player.get("byteSequence"))
        if player.get("byteSequence").startswith(b'\x00@'):
            solo_players.append((battletag, account_level))
        else:
            party_id = player.get("byteSequence")[:12]
            party_groups[party_id].append((battletag, account_level))

    return solo_players, party_groups


with open('./test-data/few replays/2024-09.StormReplay', 'rb') as file:
    # mpyq = mpyq.MPQArchive('./test-data/few replays/two.StormReplay')
    mpyq = mpyq.MPQArchive('./test-data/few replays/2024-09.StormReplay')
    battlelobby = mpyq.read_file('replay.server.battlelobby')

    # Adjusted regex to work with byte strings (ASCII-safe)
    battletag_pattern = re.compile(rb'([\w\-\_\.]+#[0-9]{4,5})')

    # Find all matches for battletags in the binary data
    battletags = battletag_pattern.finditer(battlelobby)

    players = []

    # Loop through all battletags and extract the 8 bytes before the battletag and account level after
    for match in battletags:
        battletag = match.group(0).decode('utf-8', errors='ignore')  # Decode battletag from bytes to string

        # Get the position of the battletag
        start_pos = match.start()

        before_battletag_bytes = battlelobby[start_pos - 16:start_pos]

        # Get the position right after the battletag to inspect the next bytes
        after_battletag_pos = match.end()

        # Extract the next 4 bytes after the battletag for the account level
        account_level_bytes = battlelobby[after_battletag_pos:after_battletag_pos + 4]

        # Convert raw account level bytes to integer using big-endian format ('>I')
        account_level = struct.unpack('>I', account_level_bytes)[0]

        # Print the battletag, the 8 bytes before it, and the interpreted account level
        # print(f"Battletag: {battletag}, Account Level: {account_level}, 8 Bytes Before Battletag: {before_battletag_bytes}")

        players.append({"battletag": battletag, "accountLevel": account_level, "byteSequence": before_battletag_bytes})

    solo, group = group_players(players)

    print(group)


    # replay = {
    #     'ReplayBuild': 92665,  # Example build
    #     'GameMode': 'QuickMatch',  # Example game mode
    #     'ClientListByUserID': {i: {'PlayerCollectionDictionary': {}} for i in range(16)},  # Initialize clients
    #     'DisabledHeroes': [],
    #     'RandomValue': 0
    # }
    #
    # parse_replay(replay, battlelobby)
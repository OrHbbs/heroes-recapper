import h5py
import os


class PlayerStats:
    def __init__(self, recapper_dir):
        self.file_path = os.path.join(recapper_dir, 'player_stats.h5')
        self.h5file = h5py.File(self.file_path, 'a')
        if "players" not in self.h5file:
            self.players_group = self.h5file.create_group("players")
        else:
            self.players_group = self.h5file["players"]

    def close(self):
        self.h5file.close()

    def update_player_stats(self, battletag, version, match_type, hero, won, date):
        """Update the win/loss stats for a player's hero, grouped by version and match type."""

        if battletag not in self.players_group:
            player_group = self.players_group.create_group(battletag)
        else:
            player_group = self.players_group[battletag]

        if 'games_played' not in player_group.attrs:
            player_group.attrs['games_played'] = 1
        else:
            print("adding")
            player_group.attrs['games_played'] += 1

        if 'last_played' not in player_group.attrs or player_group.attrs['last_played'] > date:
            player_group.attrs['last_played'] = str(date)

        if version not in player_group:
            version_group = player_group.create_group(version)
        else:
            version_group = player_group[version]

        if match_type not in version_group:
            match_group = version_group.create_group(match_type)
        else:
            match_group = version_group[match_type]

        if hero not in match_group:
            hero_data = match_group.create_group(hero)
            hero_data.attrs['wins'] = 1 if won else 0
            hero_data.attrs['losses'] = 0 if won else 1
        else:
            hero_data = match_group[hero]
            if won:
                hero_data.attrs['wins'] += 1
            else:
                hero_data.attrs['losses'] += 1

    def process_new_match(self, match_data):
        """Process a new match and update player stats based on the version and match type."""

        # pprint.pp(match_data)

        version = match_data.get('version')
        match_type = match_data.get('gameMode')
        date = match_data.get('date')

        print(version)

        for i in range(1, 11):
            prefix = f"{i}_"
            battletag = match_data.get(f"{prefix}battletag")
            hero = match_data.get(f"{prefix}hero")
            won = match_data.get('1_result') == 1 if i <= 5 else match_data.get('1_result') == 0  # Adjust for team

            self.update_player_stats(battletag=battletag, version=version, match_type=match_type, hero=hero, won=won, date=date)

    def get_player_stats(self, battletag):
        """returns the hdf5 structure as an object with the same structure"""
        if battletag not in self.players_group:
            return None

        player_group = self.players_group[battletag]

        stats = {
            'games_played': player_group.attrs['games_played'],
            'last_played': player_group.attrs['last_played'],
            'heroes': {}
        }

        for version in player_group:

            version_group = player_group[version]

            for match_type in version_group:
                match_group = version_group[match_type]

                for hero in match_group:
                    hero_data = match_group[hero]

                    if hero not in stats['heroes']:
                        stats['heroes'][hero] = {
                            'wins': hero_data.attrs['wins'],
                            'losses': hero_data.attrs['losses'],
                            'versions': {}
                        }

                    stats['heroes'][hero]['versions'][version] = {
                        'match_type': match_type,
                        'wins': hero_data.attrs['wins'],
                        'losses': hero_data.attrs['losses']
                    }

        return stats

    def get_all_battletags(self):
        battletags = []

        for tags in self.players_group:
            battletags.append(tags)

        return battletags

    def print_hdf5_contents(self):
        """Recursively prints contents of the hdf5 file, including attributes."""
        def print_group(group, indent=0):
            for key in group:
                item = group[key]
                if isinstance(item, h5py.Group):
                    print(f"{'  ' * indent}Group: {key}")
                    # Print attributes if any exist for this group
                    if item.attrs:
                        print(f"{'  ' * (indent + 1)}Attributes:")
                        for attr, value in item.attrs.items():
                            print(f"{'  ' * (indent + 2)}{attr}: {value}")
                    print_group(item, indent + 1)

        print("HDF5 File Contents:")
        print_group(self.h5file)

import json
import os


class Cache():
    """Cache handler

    Saves and retrieves a data dictionary to a cache file. Supports dot
    notation to get and set dictionary fields.

    """
    def __init__(self, cfg_dir, filename=".cache"):
        """Cache constructor

        Args:
            cfg_dir : Directory where the .update is located/created

        """
        self.path = os.path.join(cfg_dir, filename)
        self.data = {}
        self.load()

    def load(self):
        """Load data from the cache file"""
        if (not os.path.exists(self.path)):
            return

        with open(self.path, 'r') as fd:
            self.data = json.load(fd)

    def save(self):
        """Save data into the cache file

        Args:
            cli_update : Version of a new CLI version available for update,
                         if any

        """
        with open(self.path, 'w') as fd:
            json.dump(self.data, fd)

    def get(self, field):
        """Get using dot notation"""
        nested_keys = field.split('.')
        tmp = self.data
        for i, key in enumerate(nested_keys):
            if key not in tmp:
                return None
            if i == len(nested_keys) - 1:
                return tmp[key]
            tmp = tmp[key]

    def set(self, field, val, overwrite=True):
        """Set using dot notation"""
        nested_keys = field.split('.')
        tmp = self.data
        for i, key in enumerate(nested_keys):
            if key not in tmp:
                tmp[key] = {}
            if i == len(nested_keys) - 1:
                if (key in tmp and not overwrite):
                    return
                tmp[key] = val
            tmp = tmp[key]

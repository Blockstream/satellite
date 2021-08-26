import os
import unittest
from datetime import datetime
from . import update


class TestUpdate(unittest.TestCase):
    def tearDown(self):
        os.remove("/tmp/.update")

    def test_cache_file(self):
        test_dir = "/tmp/"
        update_cache = update.UpdateCache(test_dir)
        datetime_s = datetime.now()

        # At first, there should be no ".update" file to load. Hence, the cache
        # object should not have any data.
        self.assertFalse(update_cache.data)

        # Save the cache. This step should create the ".update" file.
        update_cache.save()
        self.assertTrue(os.path.exists(update_cache.path))

        # Now load the newly created ".update" file.
        update_cache2 = update.UpdateCache(test_dir)

        # In this case, the data should be available already.
        self.assertTrue(update_cache2.data)

        # There shouldn't be any update
        self.assertFalse(update_cache2.has_update())

        # The last update check date should be set
        datetime_e = datetime.now()
        assert (update_cache2.last_check() > datetime_s)
        assert (update_cache2.last_check() < datetime_e)

import os
import unittest
from . import cache


class TestCache(unittest.TestCase):
    def setUp(self):
        self.test_dir = "/tmp/"

    def tearDown(self):
        os.remove(os.path.join(self.test_dir, ".cache"))

    def test_cache_file(self):
        """Test cache file load/save operations"""
        cache_obj = cache.Cache(self.test_dir)

        # At first, there should be no cache file to load.
        self.assertFalse(os.path.exists(cache_obj.path))

        # Hence, the cache data dictionary should be empty.
        self.assertFalse(cache_obj.data)

        # Create the ".cache" file.
        cache_obj.save()
        self.assertTrue(os.path.exists(cache_obj.path))

        # The cache file should still be empty:
        cache_obj2 = cache.Cache(self.test_dir)
        self.assertFalse(cache_obj2.data)

        # Save some data
        cache_obj2.data['test'] = 'test'
        cache_obj2.save()

        # Load one more time and check the data:
        cache_obj3 = cache.Cache(self.test_dir)
        self.assertEqual(cache_obj3.data['test'], 'test')

    def test_dot_notation(self):
        """Test setter/getter using dot notation for nested dicts"""
        cache_obj = cache.Cache(self.test_dir)

        # Try to get a non-existing nested field
        res = cache_obj.get('a.b.c')
        self.assertIsNone(res)

        # Define a nested field
        cache_obj.set('a.b.c', 10)
        self.assertEqual(cache_obj.data['a']['b']['c'], 10)

        # Save to the cache file
        cache_obj.save()

        # Load and check the data:
        cache_obj = cache.Cache(self.test_dir)
        self.assertEqual(cache_obj.get('a.b.c'), 10)

        # Try to write an existing field with disabled overwriting
        cache_obj.set('a.b.c', 12, overwrite=False)
        self.assertEqual(cache_obj.get('a.b.c'), 10)

        # Now, allow the overwriting (the default)
        cache_obj.set('a.b.c', 12)
        self.assertEqual(cache_obj.get('a.b.c'), 12)

        # Save, reload, and check one more time
        cache_obj.save()
        cache_obj = cache.Cache(self.test_dir)
        self.assertEqual(cache_obj.get('a.b.c'), 12)

        # Try set/get with a non-nested field
        self.assertIsNone(cache_obj.get('d'))
        cache_obj.set('d', 100)
        self.assertEqual(cache_obj.data['d'], 100)

        # Save, reload, and check
        cache_obj.save()
        cache_obj = cache.Cache(self.test_dir)
        self.assertEqual(cache_obj.get('d'), 100)

        # Make sure the non-tested field did not erase the previous field
        self.assertEqual(cache_obj.get('a.b.c'), 12)

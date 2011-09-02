#!/usr/bin/env python
from configuration import Configuration

def loadTestingConfig():
    filename = "../CodeNotifier_config.py"
    return Configuration(filename, True)

import unittest
class ConfigurationTest(unittest.TestCase):
    def __checkExists(self, value):
        self.assertTrue(len(value) > 5)

    def testNoConfig(self):
        config = Configuration("blahblahcantexist")
        self.assertEquals(config.BITLY_USER, "")
        self.assertEquals(config.BITLY_KEY, "")
        self.assertEquals(config.TWIT_TOKEN, "")
        self.assertEquals(config.TWIT_SECRET, "")
        self.assertEquals(config.SVN_FS_ROOT, "")
        self.assertEquals(config.SVN_TRAC_FORMAT, "")
        self.__checkExists(config.APP_KEY)
        self.__checkExists(config.APP_SECRET)
        self.assertEqual(config.normalizeUser('bob'), 'bob')

    def testSetup(self):
        config = loadTestingConfig()
        self.__checkExists(config.BITLY_USER)
        self.__checkExists(config.BITLY_KEY)
        self.__checkExists(config.TWIT_TOKEN)
        self.__checkExists(config.TWIT_SECRET)
        self.__checkExists(config.SVN_FS_ROOT)
        self.__checkExists(config.SVN_TRAC_FORMAT)
        self.__checkExists(config.APP_KEY)
        self.__checkExists(config.APP_SECRET)
        self.assertEqual(config.normalizeUser('bob'), 'bob')

if __name__ == "__main__":
    unittest.main()

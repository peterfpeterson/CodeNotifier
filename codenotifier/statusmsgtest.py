#!/usr/bin/env python

from statusmsg import StatusMsg
from configurationtest import loadTestingConfig
import unittest

SHORT_TEXT = "this text is short"
LONG_TEXT = "Really long message that doesn't say much of anything " \
            + "but goes on and on into the ether and never comes back"
URL = " http://twitter.com"

class StatusMsgTest(unittest.TestCase):
    def setUp(self):
        self.__config = loadTestingConfig()

    def testShort(self):
        msg = StatusMsg(self.__config, SHORT_TEXT)
        self.assertEquals(str(msg), SHORT_TEXT)

    def testLong(self):
        msg = StatusMsg(self.__config, LONG_TEXT)
        self.assertEquals(str(msg), LONG_TEXT[:140])

    def testShortUrl(self):
        msg = StatusMsg(self.__config, SHORT_TEXT + URL)
        self.assertEquals(str(msg)[:len(SHORT_TEXT)], SHORT_TEXT)

    def testLongUrl(self):
        msg = StatusMsg(self.__config, LONG_TEXT + URL)
        self.assertEquals(str(msg)[:100], LONG_TEXT[:100])

if __name__ == "__main__":
    unittest.main()

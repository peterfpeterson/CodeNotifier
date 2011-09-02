#!/usr/bin/env python

from emailmsg import EmailMsg
from configurationtest import loadTestingConfig
import unittest

EMAIL_TEXT = """                                                                                                                                                                                                                                                              
Delivered-To: recipient@madeuphost.com
Date: Wed, 22 Sep 2010 10:57:03 -0400
From: noresponse@madeuphost.com
Subject: Really important email
To: recipient@madeuphost.com
Message-id: <E1032DC8-D7C6-432F-9FC4-81EEF11B116C@ornl.gov>
MIME-version: 1.0
Content-type: text/plain; charset=us-ascii
Content-language: en-US
Content-transfer-encoding: quoted-printable
Thread-Topic: Really important email
Thread-Index: ActaZmsp9vWaef2rSW+S9FoDBybkZQ==
Accept-Language: en-US
acceptlanguage: en-US
X-MS-Has-Attach:
X-MS-TNEF-Correlator:

stuffy stuff
"""

class EmailMsgTest(unittest.TestCase):
    def setUp(self):
        config = loadTestingConfig()
        self.msg = EmailMsg(config, EMAIL_TEXT, emailFrom="string")

    def testSubject(self):
        self.assertEquals(self.msg.subject, "Really important email")

    def testTime(self):
        self.assertEquals(self.msg.time, "Wed, 22 Sep 2010 10:57:03 -0400")

    def testSender(self):
        self.assertEquals(self.msg.sender, "noresponse@madeuphost.com")

    def testEncoding(self):
        self.assertEquals(self.msg.encoding, "quoted-printable")

    def testBody(self):
        self.assertEquals(self.msg.body.strip(), "stuffy stuff")

if __name__ == "__main__":
    unittest.main()

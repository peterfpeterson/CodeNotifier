#!/usr/bin/env python
#from oauth import oauth
from CodeNotifier_config import *
from oauthtwitter import OAuthApi
import pprint

class WebError(Exception):
    def __init__(self, message, code=None):
        self.__msg__ = message
        self.__code__ = code

    def __str__(self):
        if self.__code__ is not None:
            return "[%s] %s" % (self.__code__, self.__msg__)
        else:
            return self.__msg__

def composeUrl(base, params):
    import urllib
    return "%s%s" % (base, urllib.urlencode(params))

def fetchUrl(url):
    import urllib
    url_data = urllib.urlopen(url).read()
    import simplejson
    return simplejson.loads(url_data)

def getTags(links):
    if links is None:
        return []
    links = [link.longurl for link in links]
    tags = []
    for link in links:
        if "flathead" in link:
            TRAC = r'/trac'
            start = link.index(TRAC)+ len(TRAC) + 1
            stop = link.index(r'/', start)
            tags.append("#%s" % link[start:stop])
        if "ticket" in link:
            tags.append("#trac")
        if "changeset" in link:
            tags.append("#svn")
    return ' '.join(tags)

class BitlyUrl:
    def __init__(self, longurl):
        if longurl is None or len(longurl) <= 0:
            raise RuntimeError("Cannot shorten empty string")
        self.longurl = longurl
        self.shorturl = self.__shortenUrl()
    def __shortenUrl(self):
        resturl = composeUrl("http://api.bit.ly/v3/shorten?",
                             {"longUrl":self.longurl,
                              "format":"json",
                              "login":BITLY_USER,
                              "apiKey":BITLY_KEY})
        data = fetchUrl(resturl)
        self.__checkError(data)
        return data['data']['url']

    def __checkError(self, data):
        if data.get('status_code') == 200:
            return
        if data.get('status_txt') == 'OK':
            return
        raise WebError(data.get('status_txt'), data.get('status_code'))

    def __str__(self):
        return self.shorturl

    def __repr__(self):
        return self.shorturl

    def __len__(self):
        return len(self.shorturl)

class StatusMsg:
    def __init__(self, status, consumer_key=r'pfAHwsfJxkyzR25oLw13VQ',
                 consumer_secret=r'ANihRKuKtubyhH4PZsZIHOVNNoxWomKJeSuOAdodH8c'):
        self.__consumer_key = consumer_key
        self.__consumer_secret = consumer_secret
        self.msg = status
        self.__processLinks()
        self.__abbridgeMsg()

    def __processLinks(self):
        import re
        self.links = re.findall(r'https?://.+$', self.msg)
        self.links = [BitlyUrl(link) for link in self.links]
        for link in self.links:
            self.msg = self.msg.replace(link.longurl, link.shorturl)
        self.tags = getTags(self.links)
        self.msg = ' '.join((self.msg, self.tags))

    def __abbridgeMsg(self):
        '''This assumes that nothing compresible comes after the first link.'''
        if len(self.msg) < 140: # no need to shorten
            return
        index = self.msg.index(r'http://bit.ly/')
        (msg, incomp) = (self.msg[:index].strip(), self.msg[index:].strip())
        msg = msg[:140-len(incomp)-1].strip()
        self.msg = "%s %s" % (msg, incomp)

    def __str__(self):
        return self.msg

    def send(self):
        twitter = OAuthApi(self.__consumer_key, self.__consumer_secret,
                           TWIT_TOKEN, TWIT_SECRET)
        print "%s \"%s\"" % (twitter.UpdateStatus(self.msg), self.msg)

"""
twitter = OAuthApi(consumer_key, consumer_secret)

# Get the temporary credentials for our next few calls
temp_credentials = twitter.getRequestToken()

# User pastes this into their browser to bring back a pin number
print(twitter.getAuthorizationURL(temp_credentials))

# Get the pin # from the user and get our permanent credentials
oauth_verifier = raw_input('What is the PIN? ')
access_token = twitter.getAccessToken(temp_credentials, oauth_verifier)

print("oauth_token: " + access_token['oauth_token'])
print("oauth_token_secret: " + access_token['oauth_token_secret'])
"""

if __name__ == "__main__":
    status = "xuy blah blah Rearranged commands for ProcessSNSRun chain. This resolves ticket #1026. "
    tracurl = "https://flathead.ornl.gov/trac/TranslationService/ticket/1026"
    svnurl = "https://flathead.ornl.gov/trac/TranslationService/changeset/5050/"

    msg = StatusMsg(status + tracurl)
    print "TRAC:", msg
    msg.send()

    msg = StatusMsg(status + svnurl)
    print "SVN:", msg
    #msg.send()

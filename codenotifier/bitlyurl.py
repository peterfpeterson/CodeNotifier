import urllib
import simplejson

class BitlyUrl:
    def __init__(self, config, longurl, debug=0):
        self.debug = debug
        self.__BITLY_USER = config.BITLY_USER
        self.__BITLY_KEY = config.BITLY_KEY
        if longurl is None or len(longurl) <= 0:
            raise RuntimeError("Cannot shorten empty string")
        self.longurl = longurl
        self.shorturl = self.__shortenUrl()


    def composeUrl(self, base, params):
        return "%s%s" % (base, urllib.urlencode(params))

    def fetchUrl(self, url):
        url_data = urllib.urlopen(url).read()
        if url_data == None or len(url_data) <= 0:
            raise WebError("URL read failed to return anything")
        return simplejson.loads(url_data)

    def __shortenUrl(self):
        if self.debug > 1:
            return self.longurl

        resturl = self.composeUrl("http://api.bit.ly/v3/shorten?",
                                  {"longUrl":self.longurl,
                                   "format":"json",
                                   "login":self.__BITLY_USER,
                                   "apiKey":self.__BITLY_KEY})
        data = self.fetchUrl(resturl)
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

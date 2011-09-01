import re

class StatusMsg:
    FLATHEAD = "flathead"

    def __init__(self, config, status=None, **kwargs):
        # get the various keys from the kwargs list
        self.debug = kwargs.get('debug', 0)
        app_key = kwargs.get("app_key", config.APP_KEY)
        app_secret = kwargs.get("app_secret", config.APP_SECRET)
        user_key = kwargs.get("user_key", config.TWIT_TOKEN)
        user_secret = kwargs.get("user_secret", config.TWIT_SECRET)

        from oauthtwitter import OAuthApi
        self.__twitter = OAuthApi(app_key, app_secret, user_key, user_secret)
        if status is not None:
            self.setMsg(status)

    def getTags(self, tags=[]):
        if self.links is None:
            return []
        self.links = [link.longurl for link in self.links]
        for link in self.links:
            if FLATHEAD in link:
                TRAC = r'/trac'
                start = link.index(TRAC)+ len(TRAC) + 1
                stop = link.index(r'/', start)
                tags.append("#%s" % link[start:stop])
            if "ticket" in link:
                tags.append("trac")
            if "changeset" in link:
                tags.append("svn")
        return ' '.join(tags)

    def setMsg(self, status, tags=[]):
        self.msg = status
        if len(self.msg) <= 0:
            return
        self.__processLinks(tags)
        self.__abbridgeMsg()
        self.msg = self.msg.strip()
        
    def __processLinks(self, tags):
        self.links = re.findall(r'https?://.+$', self.msg)
        self.links = [BitlyUrl(link, debug=self.debug) for link in self.links]
        for link in self.links:
            self.msg = self.msg.replace(link.longurl, link.shorturl)
        self.tags = self.getTags(tags)
        self.msg = ' '.join((self.msg, self.tags))

    def __abbridgeMsg(self):
        '''This assumes that nothing compresible comes after the first link.'''
        if len(self.msg) < 140: # no need to shorten
            return
        try:
            index = self.msg.index(r'http://bit.ly/')
        except ValueError:
            index = 140
        (msg, incomp) = (self.msg[:index].strip(), self.msg[index:].strip())
        msg = msg[:140-len(incomp)-1].strip()
        self.msg = "%s %s" % (msg, incomp)

    def __str__(self):
        return self.msg

    def send(self):
        if (self.msg is not None) and (len(self.msg) > 0):
            import urllib2
            try:
                return self.__twitter.UpdateStatus(self.msg)
            except urllib2.HTTPError, e:
                print "Update '%s' failed. Reason '%s'" % (self.msg, e.info)
                raise

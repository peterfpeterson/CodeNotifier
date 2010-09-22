#!/usr/bin/env python
SVNLOOK = "/usr/bin/svnlook"
CONFIG_FILE = "CodeNotifier_config.py"

def readConfig():
    import os
    if os.path.exists(CONFIG_FILE):
        execfile(CONFIG_FILE, __builtins__.globals())
    else:
        print "Cannot read configuration file", CONFIG_FILE
        print "Please configure the application"
        import sys
        sys.exit(-1)

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

FLATHEAD = "flathead"

def getTags(links):
    if links is None:
        return []
    links = [link.longurl for link in links]
    tags = []
    for link in links:
        if FLATHEAD in link:
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

APP_KEY=r'pfAHwsfJxkyzR25oLw13VQ'
APP_SECRET=r'ANihRKuKtubyhH4PZsZIHOVNNoxWomKJeSuOAdodH8c'

class StatusMsg:
    def __init__(self, status=None, **kwargs):
        # get the various keys from the kwargs list
        app_key = kwargs.get("app_key", APP_KEY)
        app_secret = kwargs.get("app_secret", APP_SECRET)
        user_key = kwargs.get("user_key", TWIT_TOKEN)
        user_secret = kwargs.get("user_secret", TWIT_SECRET)

        from oauthtwitter import OAuthApi
        self.__twitter = OAuthApi(app_key, app_secret, user_key, user_secret)
        if status is not None:
            self.setMsg(status)

    def setMsg(self, status):
        self.msg = status
        if len(self.msg) <= 0:
            return
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
        if (self.msg is not None) and (len(self.msg) > 0):
            return self.__twitter.UpdateStatus(self.msg)

class SvnMsg(StatusMsg):
    def __init__(self, repos, rev, **kwargs):
        StatusMsg.__init__(self, **kwargs)
        self.__getCommit(repos, rev)

    def svnlook(self, indicator, changeset, command):
        cmd = "%s %s -r %d %s" % (SVNLOOK, command, int(changeset), 
                                    indicator)
        import subprocess as sub
        proc = sub.Popen(cmd, stdout=sub.PIPE, stderr=sub.PIPE, shell=True)
        return_code = proc.wait()
        (stdout, stderr) = proc.communicate()
        return stdout.strip() 

    def __getCommit(self, repos, rev):
        import os
        repos_fs = os.path.join(SVN_FS_ROOT, repos)

        author = self.svnlook(repos_fs, rev, "author")
        log = self.svnlook(repos_fs, rev, "log")
        url = SVN_TRAC_FORMAT % (repos, int(rev))

        if self.__refsTicket(log):
            self.setMsg("")
        else:
            self.setMsg(" ".join((author, log, url)))

    def __refsTicket(self, log):
        import re
        tickets = re.findall(r'#\d+', log)
        return len(tickets) > 0

class TracMsg(StatusMsg):
    def __init__(self, email_msg):
        text = email_msg.as_string()
        result = []

        # get all of the information
        author = self.__getAuthor(text)
        if len(author) > 0:
            result.append(author)
        log = self.__getLog(text)
        if len(log) > 0:
            result.append(log)
        url = self.__getUrl(text)
        if len(url) > 0:
            result.append(url)
        if len(url) <= 0 or FLATHEAD in url:
            result.append(self.__getProj(text))

        # set the message
        if len(result) > 0:
            self.setMsg(' '.join(result))
        else:
            self.setMsg("")

    def __getAuthor(self, text):
        import re

        # first look for a changeset
        answer = re.findall(r'Changes\s*\(by\s*(.+)\)', text)
        if len(answer) > 0:
            return answer[0].strip()

        # then look for a comment
        answer = re.findall(r'Comment\s*\(by\s*(.+)\)', text)
        if len(answer) > 0:
            return answer[0].strip()

        # now the person that owns it
        answer = re.findall(r'\s+Owner:\s*(.+)', text)
        if len(answer) > 0:
            return answer[0].strip()
        
        return ""

    def __getUrl(self, text):
        import re
        answer = re.findall(r'Ticket URL:\s+<(.+)>', text)
        if len(answer) <= 0:
            return ""
        link = answer[0]

        # drop the link to the comment
        if '#' in link:
            stop = link.index('#')
            link = link[:stop]

        # format the link
        if link.startswith("http"):
            return link
        else:
            return ""

    def __getLog(self, text):
        import re
        oneline = re.sub(r'\s+', ' ', text)

        answer = re.findall(r'Comment.*\(.+\):\s+(.+)--', oneline)
        if len(answer) > 0:
            return self.__trimLog(answer[0])

        answer = re.findall(r'Comment:\s+(.+)--', oneline)
        if len(answer) > 0:
            return self.__trimLog(answer[0])

        return ""

    def __trimLog(self, text):
        return text.strip()

    def __getProj(self, text):
        import re
        answer = re.findall(r'(.+\s+)<.*>', text)
        project = answer[-1].strip()
        return '#' + project.replace(' ', '')

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

def getToken():
    pass

if __name__ == "__main__":
    readConfig()

    import sys
    if sys.argv[1] == "svn":
        (repos, rev) = sys.argv[2:]
        msg = SvnMsg(repos, rev)
    elif sys.argv[1] == "trac":
        import email
        email_msg = email.message_from_file(sys.stdin)
        msg = TracMsg(email_msg)
    else:
        print "need to specify either 'svn' or 'trac' as mode"
        sys.exit(-1)
    print msg

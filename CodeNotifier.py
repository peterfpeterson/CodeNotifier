#!/usr/bin/env python
SVNLOOK = "/usr/bin/svnlook"
CONFIG_FILE = "CodeNotifier_config.py"
VERSION = "1.0"

import email
import re
import sys

def readConfig(filename, errorout=True):
    import os
    if os.path.exists(filename):
        execfile(filename, __builtins__.globals())
    else:
        if errorout:
            print "Cannot read configuration file", filename
            print "Please configure the application"
            sys.exit(-1)

def getValueFromUser(config, key, query, default=None):
    if config[key] is None or len(config[key]) <= 0:
        if default is not None:
            print "%s [%s] " % (query, default) ,
        else:
            print query, 

        config[key] = sys.stdin.readline().strip()
        if default is not None and len(config[key]) <= 0:
            config[key] = default

def generateConfig(filename):
    # read the existing settings
    readConfig(filename, False)
    config = {}
    try:
        config['BITLY_USER'] = BITLY_USER
    except NameError:
        config['BITLY_USER'] = ''
    try:
        config['BITLY_KEY'] = BITLY_KEY
    except NameError:
        config['BITLY_KEY'] = ''
    try:
        config['TWIT_TOKEN'] = TWIT_TOKEN
    except NameError:
        config['TWIT_TOKEN'] = ''
    try:
        config['TWIT_SECRET'] = TWIT_SECRET
    except NameError:
        config['TWIT_SECRET'] = ''
    try:
        config['SVN_FS_ROOT'] = SVN_FS_ROOT
    except NameError:
        config['SVN_FS_ROOT'] = ''
    try:
        config['SVN_TRAC_FORMAT'] = SVN_TRAC_FORMAT
    except NameError:
        config['SVN_TRAC_FORMAT'] = ''

    # get the bitly information
    getValueFromUser(config, 'BITLY_USER', "bit.ly username: ")
    getValueFromUser(config, 'BITLY_KEY',
                     "api key from 'http://bit.ly/a/account': ")

    # get the twitter information
    from oauthtwitter import OAuthApi
    twitter = OAuthApi(APP_KEY, APP_SECRET)
    temp_creds = twitter.getRequestToken()
    print "visit '%s' and write the pin:" % twitter.getAuthorizationURL(temp_creds)
    oauth_verifier = sys.stdin.readline().strip()
    access_token = twitter.getAccessToken(temp_creds, oauth_verifier)
    config['TWIT_TOKEN'] = access_token['oauth_token']
    config['TWIT_SECRET'] = access_token['oauth_token_secret']

    # get the svn information
    getValueFromUser(config, 'SVN_FS_ROOT', "Root directory for svn: ", '/svn/')
    getValueFromUser(config, 'SVN_TRAC_FORMAT', "Format for trac svn urls: ",
                    "http://trac.edgewall.org/changeset/%d")

    # write out the configuration
    handle = open(filename, 'w')
    keys = config.keys()
    keys.sort()
    for key in keys:
        handle.write("%s='%s'\n" % (key, config[key]))
    handle.write("def normalizeUser(user):\n")
    handle.write("    return user\n")
    handle.close()

def getProperty(text, regexp, retArray=False):
    answer = re.findall(regexp, text, re.MULTILINE)
    if len(answer) > 0:
        # cleanup whitespace
        answer = [re.sub(r'\s+', ' ', item) for item in answer]
        answer = [item.strip() for item in answer]

        if retArray:
            return answer
        else:
            return answer[0]
    return ""

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
    if url_data == None or len(url_data) <= 0:
        raise WebError("URL read failed to return anything")
    import simplejson
    return simplejson.loads(url_data)

FLATHEAD = "flathead"

def getTags(links, tags=[]):
    if links is None:
        return []
    links = [link.longurl for link in links]
    for link in links:
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

class BitlyUrl:
    def __init__(self, longurl, debug=0):
        self.debug = debug
        if longurl is None or len(longurl) <= 0:
            raise RuntimeError("Cannot shorten empty string")
        self.longurl = longurl
        self.shorturl = self.__shortenUrl()
    def __shortenUrl(self):
        if self.debug > 1:
            return self.longurl

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
        self.debug = kwargs.get('debug', 0)
        app_key = kwargs.get("app_key", APP_KEY)
        app_secret = kwargs.get("app_secret", APP_SECRET)
        user_key = kwargs.get("user_key", TWIT_TOKEN)
        user_secret = kwargs.get("user_secret", TWIT_SECRET)

        from oauthtwitter import OAuthApi
        self.__twitter = OAuthApi(app_key, app_secret, user_key, user_secret)
        if status is not None:
            self.setMsg(status)

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
        self.tags = getTags(self.links, tags)
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
        if repos.startswith(SVN_FS_ROOT):
            repos = repos.replace(SVN_FS_ROOT, '')
            repos = os.path.split(repos)[-1]
        repos_fs = os.path.join(SVN_FS_ROOT, repos)

        author = self.svnlook(repos_fs, rev, "author")
        author = normalizeUser(author)
        log = self.svnlook(repos_fs, rev, "log")
        if '%s' in SVN_TRAC_FORMAT:
            url = SVN_TRAC_FORMAT % (repos, int(rev))
        else:
            url = SVN_TRAC_FORMAT % int(rev)

        if self.__refsTicket(log):
            self.setMsg("")
        else:
            self.setMsg(" ".join((author, log, url)))

    def __refsTicket(self, log):
        tickets = re.findall(r'#\d+', log)
        return len(tickets) > 0

class EmailMsg(StatusMsg):
    def __init__(self, email_msg, **kwargs):
        StatusMsg.__init__(self, **kwargs)
        self.__email_msg__ = email_msg

    def getSubject(self):
        if 'Subject' in self.__email_msg__.keys():
            return self.__email_msg__['Subject'].strip()
        else:
            return ""

    def getEmailBody(self):
        encoding = self.__email_msg__.get('Content-Transfer-Encoding',
                                          'quoted-printable')
        if encoding == 'quoted-printable':
            return email_msg.as_string()
        elif encoding == "base64":
            import base64
            return base64.decodestring(email_msg.get_payload())
        elif encoding == "7bit":
            return email_msg.as_string()
        elif encoding == "8bit":
            return email_msg.as_string()
        else:
            raise RuntimeError("Failed to understand encoding '%s'" % encoding)

class TracMsg(EmailMsg):
    def __init__(self, email_msg, **kwargs):
        EmailMsg.__init__(self, email_msg, **kwargs)
        text = self.getEmailBody()
        result = []

        # get all of the information
        author = self.__getAuthor(text)
        if len(author) > 0:
            result.append(normalizeUser(author))
        log = self.__getLog(text)
        if " [127.0.0.1])" in log:
            log = ""
        if len(log) > 0:
            result.append(log)
        url = self.__getUrl(text)
        if len(url) > 0:
            result.append(url)
        if len(url) <= 0 or FLATHEAD in url:
            result.append(self.__getProj(text))
        ticket = self.__getTicket(url)
        if ticket is not None and ticket not in log:
            ticket = [ticket]
        else:
            ticket = []

        # set the message
        if len(result) > 0:
            self.setMsg(' '.join(result), ticket)
        else:
            self.setMsg("")

    def __getAuthor(self, text):
        # first look for a changeset
        answer = re.findall(r'Changes\s*\(by\s*(.+)\)', text)
        if len(answer) > 0:
            return answer[0].strip()

        # then look for a comment
        answer = re.findall(r'Comment\s*\(by\s*(.+)\)', text)
        if len(answer) > 0:
            return answer[0].strip()

        # see if there is an owner 
        answer = re.findall(r'Owner:\s+Type:', text)
        if len(answer) > 0:
            answer = re.findall(r'Reporter:\s*(.+)\|', text)
            if len(answer) > 0:
                return answer[0].strip()
            else:
                return ""

        # now the person that owns it
        answer = re.findall(r'\s+Owner:\s*(.+)', text)
        if len(answer) > 0:
            return answer[0].strip()

        return ""

    def __getUrl(self, text):
        # try to get it from the header
        link = self.__email_msg__.get("x-trac-ticket-url", None)

        if link is None:
            answer = re.findall(r'Ticket URL:\s+<(.+)>', text)
            if len(answer) <= 0:
                return ""
            link = answer[0]
        else:
            link = link.strip()

        # drop the link to the comment - not so useful
        '''if '#' in link:
            stop = link.index('#')
            link = link[:stop]'''

        # format the link
        if link.startswith("http"):
            return link
        elif link.startswith("hxxp"):
            return link.replace("hxxp", "http", 1)
        else:
            return ""

    def __getLog(self, text):
        oneline = re.sub(r'\s+', ' ', text)

        # look for new
        answer = re.findall(r'\|\s+Status:\s+new\s+', oneline)
        if len(answer) > 0:
            index = text.index("-------+-----")
            text = text[:index]
            answer = text.split('\n')[:-1]
            if len(answer) <= 0:
                return ""
            return "new " + self.__trimLog(answer[-1])

        # different kinds of comments
        answer = re.findall(r'Comment.*\(.+\):\s+(.+)--', oneline)
        if len(answer) > 0:
            return self.__trimLog(answer[0])

        answer = re.findall(r'Comment:\s+(.+)--', oneline)
        if len(answer) > 0:
            return self.__trimLog(answer[0])

        # just a change in status
        answer = re.findall(r'status:\s(.+)\*', oneline)
        if len(answer) > 0:
            return self.__trimLog(answer[0])

        return ""

    def __trimLog(self, text):
        if text is None:
            return ""

        text = text.strip()
        START = "{{{ #!CommitTicketReference"
        MID = 'revision="'
        STOP = "}}}"
        if START in text and MID in text and STOP in text:
            expression = '(.+)\s+%s.+%s.+"\s+(.+)\s+%s' % (START, MID, STOP)
            match = re.match(expression, text)
            text = ' '.join(match.groups())

        return text.strip()

    def __getProj(self, text):
        answer = re.findall(r'(.+\s+)<.*>', text)
        project = answer[-1].strip()
        return '#' + project.replace(' ', '')

    def __getTicket(self, url):
        # find it from the message header
        ticket = self.__email_msg__.get('x-trac-ticket-id', None)
        if ticket is not None:
            return "#%s" % ticket.strip()

        # find it from the ticket url
        answer = re.findall(r'/ticket/(\d+)#?.*', url)
        if len(answer) > 0:
            return "#%s" % answer[0]

        # give up
        return None

class NagiosMsg(EmailMsg):
    def __init__(self, email_msg, **kwargs):
        EmailMsg.__init__(self, email_msg, **kwargs)
        self.__initSubject()
        self.__initBody()
        status = [self.__subject__]
        if len(self.__info__) > 0:
            status.append(self.__info__)
        if len(self.__extra_info__) > 0:
            status.append(self.__extra_info__)
        self.setMsg(" - ".join(status))

    def __initSubject(self):
        subject = self.getSubject().strip()
        subject = re.sub(r'\s*\*+\s*', '', subject)
        subject = re.sub(r'\s+alert\s+-', ':', subject)
        subject = re.sub('/', ' ', subject)

        self.__subject__ = subject.strip()

    def __sanitize(self, text):
        if len(text) <= 0:
            return ""
        if self.__host__ in text:
            regexp = r'\(' + self.__host__ + r'.+\)'
            text = re.sub(regexp, '', text)
        return text.strip()

    def __initBody(self):
        body = self.getEmailBody()

        # get all of the keys
        self.__note_type__ = getProperty(body, r'^Notification Type:\s+(\w+)$')
        self.__host__ = getProperty(body, r'^Host:\s+(\w+)$')
        self.__state__ = getProperty(body, r'^State:\s+(\w+)$')
        self.__address__ = getProperty(body, r'^Address:\s+(\w+)$')
        self.__time__ = getProperty(body, r'^Date/Time:\s+(.+)$')
        self.__info__ = getProperty(body, r'^Info:\s+(.+)$')
        self.__extra_info__ = getProperty(body, r'^Additional Info:\s+(.+)$')

        # sanitize computer names to drop domains
        if '.' in self.__host__:
            self.__host__ = self.__host__.split('.')[0]
        self.__info__ = self.__sanitize(self.__info__)
        self.__extra_info__ = self.__sanitize(self.__extra_info__)

class TsMsg(EmailMsg):
    def __init__(self, email_msg, **kwargs):
        EmailMsg.__init__(self, email_msg, **kwargs)

        # deal with the subject line
        self.setHost()
        log = self.__parseSubject()

        if len(log) <= 0:
            log = self.__parseBody(email_msg)

        self.setMsg(log)

    def setHost(self, host = ""):
        host = host.strip()
        if len(host) <= 0:
            self.__host = ""
            return

        splitted = host.split('.')
        if len(splitted) == 3:
            self.__host = splitted[0]
        else:
            self.__host = host

    def __parseSubject(self):
        subject = self.getSubject().strip()
        if len(subject.strip()) <= 0:
            return ""

        # verify it is an existance one
        if not (subject.endswith("Does not exist") or \
                subject.endswith("Exists")):
            host = re.sub(r'\[.+\]\s+', '', subject).strip()
            self.setHost(host)
            return ""

        # format and return
        subject = re.sub(r'\[.+\]\s+', '', subject)
        subject = subject.lower()
        splitted = subject.split()
        self.setHost(splitted[0])
        subject = subject.replace(splitted[0], self.__host)

        return subject

    def __parseBody(self, email_msg):
        body = self.getEmailBody()
        formatstr = "%s failed on %s"

        # try to find TranslationError
        ts_error = re.findall(r'TranslationError:.+$', body, re.MULTILINE)
        if len(ts_error) > 0:
            ts_error = ts_error[0] # just use the first
            ts_error = ts_error.replace("TranslationError:", "")
            return formatstr % (ts_error.strip(), self.__host)

        # try to find all versions of SNSlocal in the string
        localrefs = re.findall(r'/SNSlocal/\S+', body, flags=re.MULTILINE)
        if len(localrefs) <= 0:
            return ""
        # remove quotation marks
        localrefs = [item.replace('"', '') for item in localrefs]
        localrefs = [item.replace("'", '') for item in localrefs]
        # get unique list
        localrefs = sorted(set(localrefs))
        localrefs = localrefs[0]

        # format the string
        localrefs = localrefs.replace("SNSlocal", "SNS")
        localrefs = localrefs.split("NeXus")[0]
        localrefs = localrefs.replace("pre", "")
        localrefs = localrefs[1:]
        localrefs = localrefs[0:-1]

        return formatstr % (localrefs, self.__host)

if __name__ == "__main__":
    import optparse
    info = """Send messages to twitter based on svn and trac changes. There are three fundamental commands/modes:
  [config] setup keys for posting to twitter
  [nagois] send message based on nagios update emails
  [svn] send messages based on svn updates
  [trac] send messages based on trac ticket updates
  [text] send the rest of the command line as a twitter notification"""
    parser = optparse.OptionParser("usage: %prog [command] <options>",
                                   None, optparse.Option, VERSION, 'error',
                                   info)
    parser.add_option("", "--config", dest="config", default=CONFIG_FILE)
    parser.add_option("", "--debug", dest="debug", action="count", default=0)
    (options, args) = parser.parse_args()

    modes_error="Need to specify a command: 'config', 'nagios', 'svn', " \
                + "'text', 'ts', or 'trac'"

    if len(args) <= 0:
        parser.error(modes_error)

    if "config" in args:
        generateConfig(options.config)
        sys.exit(0)

    readConfig(options.config)
    if args[0] == "svn":
        (repos, rev) = args[1:]
        msg = SvnMsg(repos, rev, debug=options.debug)
    elif args[0] == "trac":
        email_msg = email.message_from_file(sys.stdin)
        msg = TracMsg(email_msg)
    elif args[0] == "nagios":
        email_msg = email.message_from_file(sys.stdin)
        msg = NagiosMsg(email_msg)
    elif args[0] == "text":
        msg = StatusMsg(' '.join(args[1:]))
    elif args[0] == "ts":
        email_msg = email.message_from_file(sys.stdin)
        msg = TsMsg(email_msg)
    else:
        parser.error(modes_error + " (found '" + args[0] + "')")

    if options.debug:
        print msg
    else:
        msg.send()

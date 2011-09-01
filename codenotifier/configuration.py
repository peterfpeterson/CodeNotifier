import os
import sys

class Configuration:
    def __init__(self, filename, errorout=False):
        self.__config__ = {}
        self.__APP_KEY=r'pfAHwsfJxkyzR25oLw13VQ'
        self.__APP_SECRET=r'ANihRKuKtubyhH4PZsZIHOVNNoxWomKJeSuOAdodH8c'
        if os.path.exists(filename):
            result = {}
            execfile(filename, result)

            desiredkeys = ['BITLY_USER', 'BITLY_KEY', 'TWIT_TOKEN',
                           'TWIT_SECRET', 'SVN_FS_ROOT', 'SVN_TRAC_FORMAT']
            for key in desiredkeys:
                self.__config__[key] = result.get(key, '')
            self.normalizeUser = result.get('normalizeUser', lambda user: user)
        else:
            if errorout:
                print "Cannot read configuration file", filename
                print "Please configure the application"
                sys.exit(-1)

    def getValueFromUser(self, key, query, default=None):
        if self.__config__[key] is None or len(self.__config__[key]) <= 0:
            if default is not None:
                print "%s [%s] " % (query, default) ,
            else:
                print query, 

            self.__config__[key] = sys.stdin.readline().strip()
            if default is not None and len(self.__config__[key]) <= 0:
                self.__config__[key] = default

    def generate(self):
        # get the bitly information
        self.getValueFromUser('BITLY_USER', "bit.ly username: ")
        self.getValueFromUser('BITLY_KEY',
                              "api key from 'http://bit.ly/a/account': ")

        # get the twitter information
        from oauthtwitter import OAuthApi
        twitter = OAuthApi(self.__APP_KEY, self.__APP_SECRET)
        temp_creds = twitter.getRequestToken()
        print "visit '%s' and write the pin:" \
            % twitter.getAuthorizationURL(temp_creds)
        oauth_verifier = sys.stdin.readline().strip()
        access_token = twitter.getAccessToken(temp_creds, oauth_verifier)
        config['TWIT_TOKEN'] = access_token['oauth_token']
        config['TWIT_SECRET'] = access_token['oauth_token_secret']

        # get the svn information
        self.getValueFromUser('SVN_FS_ROOT', "Root directory for svn: ",
                              '/svn/')
        self.getValueFromUser('SVN_TRAC_FORMAT',
                              "Format for trac svn urls: ",
                              "http://trac.edgewall.org/changeset/%d")

        # write out the configuration
        handle = open(filename, 'w')
        keys = self.__config__.keys()
        keys.sort()
        for key in keys:
            handle.write("%s='%s'\n" % (key, config[key]))
        handle.write("def normalizeUser(user):\n")
        handle.write("    return user\n")
        pphandle.close()

    def __str__(self):
        result = []
        for key in self.__config__.keys():
            result.append("%s:%s" % (key, self.__config__[key]))
        return "\n".join(result)

    # declare all of the properties
    SVN_FS_ROOT = property(lambda self: self.__config__['SVN_FS_ROOT'])
    BITLY_USER = property(lambda self: self.__config__['BITLY_USER'])
    BITLY_KEY = property(lambda self: self.__config__['BITLY_KEY'])
    TWIT_TOKEN = property(lambda self: self.__config__['TWIT_TOKEN'])
    TWIT_SECRET = property(lambda self: self.__config__['TWIT_SECRET'])
    SVN_FS_ROOT = property(lambda self: self.__config__['SVN_FS_ROOT'])
    SVN_TRAC_FORMAT = property(lambda self: self.__config__['SVN_TRAC_FORMAT'])
    APP_KEY = property(lambda self: self.__APP_KEY)
    APP_SECRET = property(lambda self: self.__APP_SECRET)

def loadTestingConfig():
    filename = "../CodeNotifier_config.py"
    print "Test program requires '%s' to exist" % filename
    return Configuration(filename, True)

if __name__ == "__main__":
    config = loadTestingConfig()
    print "***"
    print config
    print "***", config.SVN_FS_ROOT
    print "***", config.APP_KEY
    print "***", config.normalizeUser('bob')

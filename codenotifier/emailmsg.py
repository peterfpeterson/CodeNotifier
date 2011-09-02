from statusmsg import StatusMsg
import email

class EmailMsg:
    def __init__(self, email_msg, **kwargs):
        emailFrom = kwargs.get("emailFrom", "file")
        if emailFrom is None:
            self.__email_msg__ = email_msg
        elif emailFrom == "string":
            self.__email_msg__ = email.message_from_string(email_msg)
        elif emailFrom == "file":
            self.__email_msg__ = email.message_from_file(email_msg)
        else:
            raise RuntimeError("Do not know how to initialize from '%s'" % emailFrom)

        self.body = self.__getEmailBody().strip()

    def __getValue(self, key, default=""):
        if key in self.__email_msg__.keys():
            return self.__email_msg__[key].strip()
        else:
            return default

    def __getEmailBody(self):
        encoding = self.encoding
        body = self.__email_msg__.get_payload()
        if encoding == 'quoted-printable':
            return body
        elif encoding == "base64":
            import base64
            return base64.decodestring(body)
        elif encoding == "7bit":
            return body
        elif encoding == "8bit":
            return body
        else:
            raise RuntimeError("Failed to understand encoding '%s'" % encoding)

    subject = property(lambda self: self.__getValue('Subject'))
    time = property(lambda self: self.__getValue('Date'))
    sender = property(lambda self: self.__getValue('From'))
    encoding = property(lambda self: self.__getValue('Content-Transfer-Encoding',
                                                     'quoted-printable'))

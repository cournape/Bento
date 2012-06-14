class BentoError(Exception):
    pass

class InternalBentoError(BentoError):
    def __str__(self):
        return "unexpected error: %s (most likely a bento bug)"

class InvalidPackage(BentoError):
    pass

class UsageException(BentoError):
    pass

class ParseError(BentoError):
    def __init__(self, msg="", token=None):
        self.msg = msg
        self.token = token
        if token is not None:
            self.lineno = token.lineno
            self.tp = token.type
            self.value = token.value
        else:
            self.lineno = self.tp = self.value = None
        self.filename = None
        # Don't use super here because Exception are not new-class object on 2.4
        BentoError.__init__(self, msg)

    def __str__(self):
        if self.filename is None or self.token is None:
            return Exception.__str__(self)
        else:
            msg = '  File "%(file)s", line %(lineno)d\n' \
                  % {"file": self.filename, "lineno": self.lineno}
            f = open(self.filename)
            try:
                # This is expensive, there must be a better way
                cnt = f.read()
                lines = cnt.splitlines()
                linepos = sum([(len(l)+1) for l in lines[:self.lineno-1]])
                msg += "%s\n" % lines[self.lineno-1]
                pos = self.token.lexpos
                msg += " " * (pos - linepos) + "^\n"
                msg += "Syntax error"
                return msg
            finally:
                f.close()

    def __repr__(self):
        return self.__str__()

class InvalidHook(BentoError):
    pass

class CommandExecutionFailure(BentoError):
    pass

class ConfigurationError(CommandExecutionFailure):
    pass

class BuildError(CommandExecutionFailure):
    pass

class ConvertionError(BentoError):
    pass

class SetupCannotRun(ConvertionError):
    pass

class UnsupportedFeature(ConvertionError):
    pass

class InvalidPyPIConfig(BentoError):
    pass

class PyPIError(BentoError):
    pass

class InvalidRepository(PyPIError):
    pass

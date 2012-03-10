class BentoError(Exception):
    pass

class InternalBentoError(BentoError):
    def __str__(self):
        return "unexpected error: %s (most likely a bento bug)"

class InvalidPackage(BentoError):
    pass

class ConfigurationError(BentoError):
    pass

class BuildError(BentoError):
    pass

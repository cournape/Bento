class BentoError(Exception):
    pass

class InternalBentoError(BentoError):
    pass

class InvalidPackage(BentoError):
    pass

class ConfigurationError(BentoError):
    pass

class BuildError(BentoError):
    pass

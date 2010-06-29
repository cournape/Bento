class BentoError(Exception):
    pass

class InvalidPackage(BentoError):
    pass

class BuildError(BentoError):
    pass

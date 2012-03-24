import bento.core.errors

class ConvertionError(bento.core.errors.BentoError):
    pass

class SetupCannotRun(ConvertionError):
    pass

class UnsupportedFeature(ConvertionError):
    pass

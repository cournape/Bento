import bento.errors

class ConvertionError(bento.errors.BentoError):
    pass

class SetupCannotRun(ConvertionError):
    pass

class UnsupportedFeature(ConvertionError):
    pass

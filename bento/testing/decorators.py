import warnings

from bento.compat.api \
    import \
        wraps
from bento.warnings \
    import \
        NoBentoInfoWarning

def disable_warning(f):
    def decorator_factory(warning_class=UserWarning):
        @wraps(f)
        def decorator(*a, **kw):
            filters = warnings.filters[:]
            warnings.simplefilter("ignore", warning_class)
            try:
                return f(*a, **kw)
            finally:
                warnings.filters = filters
        return decorator
    return decorator_factory

disable_missing_bento_warning = lambda f: disable_warning(f)(NoBentoInfoWarning)

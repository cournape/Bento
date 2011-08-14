import os

import nose

from nose.plugins.errorclass \
    import \
        ErrorClass, ErrorClassPlugin
from nose.plugins.skip \
    import \
        SkipTest

class KnownFailureTest(Exception):
    pass

class KnownFailure(ErrorClassPlugin):
    '''Plugin that installs a KNOWNFAIL error class for the
    KnownFailureClass exception.  When KnownFailureTest is raised,
    the exception will be logged in the knownfail attribute of the
    result, 'K' or 'KNOWNFAIL' (verbose) will be output, and the
    exception will not be counted as an error or failure.'''
    enabled = True
    knownfail = ErrorClass(KnownFailureTest,
                           label='KNOWNFAIL',
                           isfailure=False)

    def options(self, parser, env=os.environ):
        env_opt = 'NOSE_WITHOUT_KNOWNFAIL'
        parser.add_option('--no-knownfail', action='store_true',
                          dest='noKnownFail', default=env.get(env_opt, False),
                          help='Disable special handling of KnownFailureTest '
                               'exceptions')

    def configure(self, options, conf):
        if not self.can_configure:
            return
        self.conf = conf
        disable = getattr(options, 'noKnownFail', False)
        if disable:
            self.enabled = False


def skipif(condition, msg=None):
    def skip_decorator(f):
        if callable(condition):
            skip_func = condition
        else:
            skip_func = lambda : condition()

        if skip_func():
            def g(*a, **kw):
                raise SkipTest()
        else:
            g = f
        return nose.tools.make_decorator(f)(g)
    return skip_decorator

# Code taken from Numpy
def knownfailureif(fail_condition, msg=None):
    """
    Make function raise KnownFailureTest exception if given condition is true.

    If the condition is a callable, it is used at runtime to dynamically
    make the decision. This is useful for tests that may require costly
    imports, to delay the cost until the test suite is actually executed.

    Parameters
    ----------
    fail_condition : bool or callable
        Flag to determine whether to mark the decorated test as a known
        failure (if True) or not (if False).
    msg : str, optional
        Message to give on raising a KnownFailureTest exception.
        Default is None.

    Returns
    -------
    decorator : function
        Decorator, which, when applied to a function, causes SkipTest
        to be raised when `skip_condition` is True, and the function
        to be called normally otherwise.

    Notes
    -----
    The decorator itself is decorated with the ``nose.tools.make_decorator``
    function in order to transmit function name, and various other metadata.

    """
    if msg is None:
        msg = 'Test skipped due to known failure'

    # Allow for both boolean or callable known failure conditions.
    if callable(fail_condition):
        fail_val = lambda : fail_condition()
    else:
        fail_val = lambda : fail_condition

    def knownfail_decorator(f):
        # Local import to avoid a hard nose dependency and only incur the
        # import time overhead at actual test-time.
        def knownfailer(*args, **kwargs):
            if fail_val():
                raise KnownFailureTest, msg
            else:
                return f(*args, **kwargs)
        return nose.tools.make_decorator(f)(knownfailer)

    return knownfail_decorator


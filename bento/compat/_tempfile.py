"""
NamedTemporaryFile with delete option for python 2.4/2.5
"""
import os as _os
from tempfile \
    import \
        gettempdir, template

# Importing private stuff is ok here as this is for compat, and won't change
# (checked that python 2.4.4 has those values, has not checked for 2.5.*, but
# 2.6.4 define those to same values...
from tempfile \
    import \
        _text_openflags, _bin_openflags, _mkstemp_inner

# Code below taken verbatim from python 2.6.4
class _TemporaryFileWrapper:
    """Temporary file wrapper

    This class provides a wrapper around files opened for
    temporary use.  In particular, it seeks to automatically
    remove the file when it is no longer needed.
    """

    def __init__(self, file, name, delete=True):
        self.file = file
        self.name = name
        self.close_called = False
        self.delete = delete

    def __getattr__(self, name):
        # Attribute lookups are delegated to the underlying file
        # and cached for non-numeric results
        # (i.e. methods are cached, closed and friends are not)
        file = self.__dict__['file']
        a = getattr(file, name)
        if not issubclass(type(a), type(0)):
            setattr(self, name, a)
        return a

    # The underlying __enter__ method returns the wrong object
    # (self.file) so override it to return the wrapper
    def __enter__(self):
        self.file.__enter__()
        return self

    # NT provides delete-on-close as a primitive, so we don't need
    # the wrapper to do anything special.  We still use it so that
    # file.name is useful (i.e. not "(fdopen)") with NamedTemporaryFile.
    if _os.name != 'nt':
        # Cache the unlinker so we don't get spurious errors at
        # shutdown when the module-level "os" is None'd out.  Note
        # that this must be referenced as self.unlink, because the
        # name TemporaryFileWrapper may also get None'd out before
        # __del__ is called.
        unlink = _os.unlink

        def close(self):
            if not self.close_called:
                self.close_called = True
                self.file.close()
                if self.delete:
                    self.unlink(self.name)

        def __del__(self):
            self.close()

        # Need to trap __exit__ as well to ensure the file gets
        # deleted when used in a with statement
        def __exit__(self, exc, value, tb):
            result = self.file.__exit__(exc, value, tb)
            self.close()
            return result


def NamedTemporaryFile(mode='w+b', bufsize=-1, suffix="",
                       prefix=template, dir=None, delete=True):
    """Create and return a temporary file.
    Arguments:
    'prefix', 'suffix', 'dir' -- as for mkstemp.
    'mode' -- the mode argument to os.fdopen (default "w+b").
    'bufsize' -- the buffer size argument to os.fdopen (default -1).
    'delete' -- whether the file is deleted on close (default True).
    The file is created as mkstemp() would do it.

    Returns an object with a file-like interface; the name of the file
    is accessible as file.name.  The file will be automatically deleted
    when it is closed unless the 'delete' argument is set to False.
    """

    if dir is None:
        dir = gettempdir()

    if 'b' in mode:
        flags = _bin_openflags
    else:
        flags = _text_openflags

    # Setting O_TEMPORARY in the flags causes the OS to delete
    # the file when it is closed.  This is only supported by Windows.
    if _os.name == 'nt' and delete:
        flags |= _os.O_TEMPORARY

    (fd, name) = _mkstemp_inner(dir, prefix, suffix, flags)
    file = _os.fdopen(fd, mode, bufsize)
    return _TemporaryFileWrapper(file, name, delete)


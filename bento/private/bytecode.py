import sys

# Utils to compile .py to .pyc inside zip file
# XXX: this is implementation detail of .pyc, copied from py_compile.py.
# Unfortunately, there is no way that I know of to write the bytecode into a
# string to be used by ZipFile (using compiler is way too slow). Also, the
# py_compile code has not changed much for 10 years.
# XXX: the code has changed quite a few times in python 3.x timeline, we need
# to keep too many copies. Maybe it is not worth it to support this feature
# altogether ?
from py_compile \
    import \
        PyCompileError
if sys.version_info[0] < 3:
    from _bytecode_2 \
        import \
            bcompile
else:
    from bento.private._bytecode_3 \
        import \
            bcompile

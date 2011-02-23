import sys

# Utils to compile .py to .pyc inside zip file
# XXX: this is implementation detail of .pyc, copied from py_compile.py.
# Unfortunately, there is no way that I know of to write the bytecode into a
# string to be used by ZipFile (using compiler is way too slow). Also, the
# py_compile code has not changed much for 10 years.
if sys.version_info[0] < 3:
    from _bytecode_2 \
        import \
            bcompile, PyCompileError
else:
    from _bytecode_3 \
        import \
            bcompile, PyCompileError

import io
import py_compile

def _bcompile(file, cfile=None, dfile=None, doraise=False):
    encoding = py_compile.read_encoding(file, "utf-8")
    f = open(file, 'U', encoding=encoding)
    try:
        timestamp = int(os.fstat(f.fileno()).st_mtime)
    except AttributeError:
        timestamp = int(os.stat(file).st_mtime)
    codestring = f.read()
    f.close()
    if codestring and codestring[-1] != '\n':
        codestring = codestring + '\n'
    try:
        codeobject = builtins.compile(codestring, dfile or file,'exec')
    except Exception as err:
        py_exc = PyCompileError(err.__class__, err, dfile or file)
        if doraise:
            raise py_exc
        else:
            sys.stderr.write(py_exc.msg + '\n')
            return
    fc = io.BytesIO()
    try:
        fc.write(b'\0\0\0\0')
        wr_long(fc, timestamp)
        marshal.dump(codeobject, fc)
        fc.flush()
        fc.seek(0, 0)
        fc.write(MAGIC)
        return fc.getvalue()
    finally:
        fc.close()

def bcompile(file):
    return _bcompile(file, doraise=True)

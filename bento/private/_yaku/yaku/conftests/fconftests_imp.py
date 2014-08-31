import os
import sys
import re
import shlex

GCC_DRIVER_LINE = re.compile('^Driving:')
POSIX_STATIC_EXT = re.compile('\S+\.a')
POSIX_LIB_FLAGS = re.compile('-l\S+')

def is_output_verbose(out):
    for line in out.splitlines():
        if not GCC_DRIVER_LINE.search(line):
            if POSIX_STATIC_EXT.search(line) or POSIX_LIB_FLAGS.search(line):
                return True
    return False

# linkflags which match those are ignored
LINKFLAGS_IGNORED = [r'-lang*', r'-lcrt[a-zA-Z0-9]*\.o', r'-lc$', r'-lSystem',
                     r'-libmil', r'-LIST:*', r'-LNO:*']
if os.name == 'nt':
    LINKFLAGS_IGNORED.extend([r'-lfrt*', r'-luser32',
            r'-lkernel32', r'-ladvapi32', r'-lmsvcrt',
            r'-lshell32', r'-lmingw', r'-lmoldname'])
else:
    LINKFLAGS_IGNORED.append(r'-lgcc*')

RLINKFLAGS_IGNORED = [re.compile(f) for f in LINKFLAGS_IGNORED]

def _match_ignore(line):
    """True if the line should be ignored."""
    if [i for i in RLINKFLAGS_IGNORED if i.match(line)]:
        return True
    else:
        return False

def parse_flink(output):
    """Given the output of verbose link of fortran compiler, this
    returns a list of flags necessary for linking using the standard
    linker."""
    # TODO: On windows ?
    final_flags = []
    for line in output.splitlines():
        if not GCC_DRIVER_LINE.match(line):
            _parse_f77link_line(line, final_flags)
    return final_flags

SPACE_OPTS = re.compile('^-[LRuYz]$')
NOSPACE_OPTS = re.compile('^-[RL]')

def _parse_f77link_line(line, final_flags):
    #line = line.encode("utf-8")
    lexer = shlex.shlex(line, posix = True)
    lexer.whitespace_split = True

    t = lexer.get_token()
    tmp_flags = []
    while t:
        def parse(token):
            # Here we go (convention for wildcard is shell, not regex !)
            #   1 TODO: we first get some root .a libraries
            #   2 TODO: take everything starting by -bI:*
            #   3 Ignore the following flags: -lang* | -lcrt*.o | -lc |
            #   -lgcc* | -lSystem | -libmil | -LANG:=* | -LIST:* | -LNO:*)
            #   4 take into account -lkernel32
            #   5 For options of the kind -[[LRuYz]], as they take one argument
            #   after, the actual option is the next token 
            #   6 For -YP,*: take and replace by -Larg where arg is the old
            #   argument
            #   7 For -[lLR]*: take

            # step 3
            if _match_ignore(token):
                pass
            # step 4
            elif token.startswith('-lkernel32') and sys.platform == 'cygwin':
                tmp_flags.append(token)
            # step 5
            elif SPACE_OPTS.match(token):
                t = lexer.get_token()
                # FIXME: this does not make any sense ... pull out
                # what we need from this section
                #if t.startswith('P,'):
                #    t = t[2:]
                #    for opt in t.split(os.pathsep):
                #        tmp_flags.append('-L%s' % opt)
            # step 6
            elif NOSPACE_OPTS.match(token):
                tmp_flags.append(token)
            # step 7
            elif POSIX_LIB_FLAGS.match(token):
                tmp_flags.append(token)
            else:
                # ignore anything not explicitely taken into account
                pass

            t = lexer.get_token()
            return t
        t = parse(t)

    final_flags.extend(tmp_flags)
    return final_flags

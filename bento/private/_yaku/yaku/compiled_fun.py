import os
import re
import sys

from yaku.environment \
    import \
        Environment

COMPILE_TEMPLATE_SHELL = '''
def f(task):
    env = task.env
    bld = task.bld
    wd = getattr(task, 'cwd', None)
    p = env.get_flat
    cmd = \'\'\' %s \'\'\' % s
    return task.exec_command(cmd, cwd=wd, env=env['ENV'])
'''

COMPILE_TEMPLATE_NOSHELL = '''
def f(task):
	env = task.env
	bld_root = task.gen.bld.bld_root
	wd = getattr(task, 'cwd', None)
	def to_list(xx):
		if isinstance(xx, str): return [xx]
		return xx
	lst = []
	%s
	lst = [x for x in lst if x]
	return task.exec_command(lst, cwd=wd, env=env['ENV'])
'''


def funex(c):
    dc = {}
    exec(c, dc)
    return dc['f']

reg_act = re.compile(r"(?P<backslash>\\)|(?P<dollar>\$\$)|(?P<subst>\$\{(?P<var>\w+)(?P<code>.*?)\})", re.M)
def compile_fun_shell(name, line):
    """Compiles a string (once) into a function, eg:
    simple_task_type('c++', '${CXX} -o ${TGT[0]} ${SRC} -I ${SRC[0].parent.bldpath()}')

    The env variables (CXX, ..) on the task must not hold dicts (order)
    The reserved keywords TGT and SRC represent the task input and output nodes

    quick test:
    bld(source='wscript', rule='echo "foo\\${SRC[0].name}\\bar"')
    """

    extr = []
    def repl(match):
        g = match.group
        if g('dollar'): return "$"
        elif g('backslash'): return '\\\\'
        elif g('subst'): extr.append((g('var'), g('code'))); return "%s"
        return None

    line = reg_act.sub(repl, line)

    parm = []
    dvars = []
    app = parm.append
    for (var, meth) in extr:
        if var == 'SRC':
            if meth:
                app('task.inputs%s' % meth)
            else:
                app('" ".join([i.path_from(bld.bldnode) for i in task.inputs)')
        elif var == 'TGT':
            if meth:
                app('task.outputs%s' % meth)
            else:
                app('" ".join([i.path_from(bld.bldnode) for i in task.outputs)')
        else:
            if not var in dvars:
                dvars.append(var)
            app("p('%s')" % var)
    if parm:
        parm = "%% (%s) " % (',\n\t\t'.join(parm))
    else:
        parm = ''

    c = COMPILE_TEMPLATE_SHELL % (line, parm)

    return (funex(c), dvars)

def compile_fun_noshell(name, line):

    extr = []
    def repl(match):
        g = match.group
        if g('dollar'): return "$"
        elif g('subst'): extr.append((g('var'), g('code'))); return "<<|@|>>"
        return None

    line2 = reg_act.sub(repl, line)
    params = line2.split('<<|@|>>')

    buf = []
    dvars = []
    app = buf.append
    for x in range(len(extr)):
        params[x] = params[x].strip()
        if params[x]:
            app("lst.extend(%r)" % params[x].split())
        (var, meth) = extr[x]
        if var == 'SRC':
            if meth: app('lst.append(task.inputs%s)' % meth)
            else:
                app('lst.extend([i.path_from(bld_root) for i in task.inputs])')
        elif var == 'TGT':
            if meth: app('lst.append(task.outputs%s)' % meth)
            else:
                app('lst.extend([i.path_from(bld_root) for i in task.outputs])')
        else:
            app('lst.extend(to_list(env.get(%r, [])))' % var)
            if not var in dvars: dvars.append(var)

    if params[-1]:
        app("lst.extend(%r)" % shlex.split(params[-1]))

    fun = COMPILE_TEMPLATE_NOSHELL % "\n\t".join(buf)
    return (funex(fun), dvars)

def compile_fun(name, line, shell=None):
    "commands can be launched by the shell or not"
    if line.find('<') > 0 or line.find('>') > 0 or line.find('&&') > 0:
        shell = True

    if shell is None:
        if sys.platform == 'win32':
            shell = False
        else:
            shell = True

    if shell:
        return compile_fun_shell(name, line)
    else:
        return compile_fun_noshell(name, line)

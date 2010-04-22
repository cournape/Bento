from cStringIO import StringIO
from cPickle import dump, load
import os, sys

from toydist.core.utils \
    import \
        pprint
from toydist.commands.configure \
    import \
        get_configured_state
from toymakerlib.hooks \
    import \
        override, post_configure

join = os.path.join

wafdir = os.getcwd()
w = join(wafdir, 'wafadmin')
t = join(w, 'Tools')
f = join(w, '3rdparty')
sys.path = [w, t, f] + sys.path

import Configure
import Utils, Options, Build
import Environment

cwd = os.getcwd()
opt_obj = Options.Handler()
opt_obj.curdir = cwd
opt_obj.tool_options('compiler_cc')
opt_obj.parse_args([])
Options.tooldir = [t]

class foo(object):
   pass
Utils.g_module = foo
Utils.g_module.root_path = cwd

Options.lockfile = ".waf.lock"
CACHEDIR = "c4che"

@post_configure
def configure_waf():
    pprint('BLUE', "Configuring waf")

    conf_log = open("config.log", "w")
    ctx = Configure.ConfigurationContext()
    ctx.log = conf_log
    ctx.srcdir = cwd
    ctx.blddir = join(cwd, 'build')
    ctx.check_tool('compiler_cc')
    ctx.check_tool('python')
    ctx.check_python_version((2, 4, 0))
    ctx.check_python_headers()
    ctx.cachedir = CACHEDIR
    #ctx.check_cc(fragment='int main() {return 0;}')
    ctx.store()

    ctx.env.store(Options.lockfile)

@override
def build(opts):
    pprint('BLUE', "Overriden build command")

    env = Environment.Environment(Options.lockfile)

    bld = Build.BuildContext()
    bld.cachedir = CACHEDIR
    bld.load()

    bld.all_envs['default'] = env
    bld.lst_variants = bld.all_envs.keys()
    bld.load_dirs(cwd, join(cwd, 'build'))
    #bld(rule="touch ${TGT}", source='main.c', target='bar.txt')
    #bld(features='cc chlib pyext', source='main.c', target='app')
    #bld.compile()

    config = get_configured_state()
    pkg = config.pkg
    for ext in pkg.extensions.values():
        bld(features='cc cshlib pyext', source=ext.sources, target=ext.name)
    bld.compile()

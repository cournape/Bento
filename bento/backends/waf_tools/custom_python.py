import os
import sys

from waflib import Utils, Options, Errors
from waflib.Configure import conf
from waflib.TaskGen import before_method, after_method, feature
from waflib.Logs import debug, warn

DISTUTILS_IMP = ['from distutils.sysconfig import get_config_var, get_python_lib']

@feature('pyext')
@before_method('apply_link', 'apply_bundle')
def set_bundle(self):
	if Utils.unversioned_sys_platform() == 'darwin':
		self.mac_bundle = True

@conf
def check_python_version(conf, minver=None):
	"""
	Check if the python interpreter is found matching a given minimum version.
	minver should be a tuple, eg. to check for python >= 2.4.2 pass (2,4,2) as minver.

	If successful, PYTHON_VERSION is defined as 'MAJOR.MINOR'
	(eg. '2.4') of the actual python version found, and PYTHONDIR is
	defined, pointing to the site-packages directory appropriate for
	this python version, where modules/packages/extensions should be
	installed.

	:param minver: minimum version
	:type minver: tuple of int
	"""
	assert minver is None or isinstance(minver, tuple)
	pybin = conf.env['PYTHON']
	if not pybin:
		conf.fatal('could not find the python executable')

	# Get python version string
	cmd = pybin + ['-c', 'import sys\nfor x in sys.version_info: print(str(x))']
	debug('python: Running python command %r' % cmd)
	lines = conf.cmd_and_log(cmd).split()
	assert len(lines) == 5, "found %i lines, expected 5: %r" % (len(lines), lines)
	pyver_tuple = (int(lines[0]), int(lines[1]), int(lines[2]), lines[3], int(lines[4]))

	# compare python version with the minimum required
	result = (minver is None) or (pyver_tuple >= minver)

	if result:
		# define useful environment variables
		pyver = '.'.join([str(x) for x in pyver_tuple[:2]])
		conf.env['PYTHON_VERSION'] = pyver

	# Feedback
	pyver_full = '.'.join(map(str, pyver_tuple[:3]))
	if minver is None:
		conf.msg('Checking for python version', pyver_full)
	else:
		minver_str = '.'.join(map(str, minver))
		conf.msg('Checking for python version', pyver_tuple, ">= %s" % (minver_str,) and 'GREEN' or 'YELLOW')

	if not result:
		conf.fatal('The python version is too old, expecting %r' % (minver,))

@conf
def get_python_variables(self, variables, imports=None):
	"""
	Spawn a new python process to dump configuration variables

	:param variables: variables to print
	:type variables: list of string
	:param imports: one import by element
	:type imports: list of string
	:return: the variable values
	:rtype: list of string
	"""
	if not imports:
		try:
			imports = self.python_imports
		except AttributeError:
			imports = DISTUTILS_IMP

	program = list(imports) # copy
	program.append('')
	for v in variables:
		program.append("print(repr(%s))" % v)
	os_env = dict(os.environ)
	try:
		del os_env['MACOSX_DEPLOYMENT_TARGET'] # see comments in the OSX tool
	except KeyError:
		pass

	try:
		out = self.cmd_and_log(self.env.PYTHON + ['-c', '\n'.join(program)], env=os_env)
	except Errors.WafError:
		self.fatal('The distutils module is unusable: install "python-devel"?')
	return_values = []
	for s in out.split('\n'):
		s = s.strip()
		if not s:
			continue
		if s == 'None':
			return_values.append(None)
		elif s[0] == "'" and s[-1] == "'":
			return_values.append(s[1:-1])
		elif s[0].isdigit():
			return_values.append(int(s))
		else: break
	return return_values

@conf
def check_python_headers(conf):
	"""
	Check for headers and libraries necessary to extend or embed python by using the module *distutils*.
	On success the environment variables xxx_PYEXT and xxx_PYEMBED are added:

	* PYEXT: for compiling python extensions
	* PYEMBED: for embedding a python interpreter
	"""

	# FIXME rewrite

	if not conf.env['CC_NAME'] and not conf.env['CXX_NAME']:
		conf.fatal('load a compiler first (gcc, g++, ..)')

	if not conf.env['PYTHON_VERSION']:
		conf.check_python_version()

	env = conf.env
	pybin = env.PYTHON
	if not pybin:
		conf.fatal('could not find the python executable')

	v = 'INCLUDEPY SO LDFLAGS MACOSX_DEPLOYMENT_TARGET LDSHARED CFLAGS'.split()
	try:
		lst = conf.get_python_variables(["get_config_var('%s') or ''" % x for x in v])
	except RuntimeError:
		conf.fatal("Python development headers not found (-v for details).")

	vals = ['%s = %r' % (x, y) for (x, y) in zip(v, lst)]
	conf.to_log("Configuration returned from %r:\n%r\n" % (pybin, '\n'.join(vals)))

	dct = dict(zip(v, lst))
	x = 'MACOSX_DEPLOYMENT_TARGET'
	if dct[x]:
		conf.env[x] = conf.environ[x] = dct[x]

	env['pyext_PATTERN'] = '%s' + dct['SO'] # not a mistake

	if Options.options.use_distutils_flags:
		all_flags = dct['LDFLAGS'] + ' ' + dct['LDSHARED'] + ' ' + dct['CFLAGS']
		conf.parse_flags(all_flags, 'PYEXT')

	env['INCLUDES_PYEXT'] = [dct['INCLUDEPY']]

@feature('pyext')
@before_method('propagate_uselib_vars', 'apply_link')
@after_method('apply_bundle')
def init_pyext(self):
	"""
	Change the values of *cshlib_PATTERN* and *cxxshlib_PATTERN* to remove the
	*lib* prefix from library names.
	"""
	self.uselib = self.to_list(getattr(self, 'uselib', []))
	if not 'PYEXT' in self.uselib:
		self.uselib.append('PYEXT')
	# override shlib_PATTERN set by the osx module
	self.env['cshlib_PATTERN'] = self.env['cxxshlib_PATTERN'] = self.env['macbundle_PATTERN'] = self.env['pyext_PATTERN']

	try:
		if not self.install_path:
			return
	except AttributeError:
		self.install_path = '${PYTHONARCHDIR}'

def configure(conf):
	"""
	Detect the python interpreter
	"""
	default = [sys.executable]
	try:
		conf.find_program('python', var='PYTHON')
	except conf.errors.ConfigurationError:
		warn("could not find a python executable, setting to sys.executable '%s'" % sys.executable)
		conf.env.PYTHON = default

	if conf.env.PYTHON != default:
		warn("python executable '%s' different from sys.executable '%s'" % (conf.env.PYTHON, default))
	conf.env.PYTHON = conf.cmd_to_list(default)

	v = conf.env
	v['PYCMD'] = '"import sys, py_compile;py_compile.compile(sys.argv[1], sys.argv[2])"'
	v['PYFLAGS'] = ''
	v['PYFLAGS_OPT'] = '-O'

def options(opt):
	opt.add_option('--use-distutils-flags',
			action='store_true',
			default=False,
			help='Use flags as defined by distutils [Default:no]',
			dest='pyc')

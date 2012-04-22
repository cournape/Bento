from waflib import Task
from waflib.TaskGen import before_method, feature, taskgen_method
from waflib.Tools import ccroot

import waflib.Tools.c

def colon(env, var1, var2):
	tmp = env[var1]
	if isinstance(var2, str):
		it = env[var2]
	else:
		it = var2
	if isinstance(tmp, str):
		return [tmp % x for x in it]
	else:
		lst = []
		for y in it:
			lst.extend(tmp)
			lst.append(y)
		return lst

@taskgen_method
def interpolate_flags(task_gen, line):
	env = task_gen.env
	reg_act = Task.reg_act

	extr = []
	def repl(match):
		g = match.group
		if g('dollar'): return "$"
		elif g('backslash'): return '\\\\'
		elif g('subst'): extr.append((g('var'), g('code'))); return "%s"
		return None

	line = reg_act.sub(repl, line) or line

	ret = []
	for (var, meth) in extr:
		if meth:
			if meth.startswith(':'):
				m = meth[1:]
				ret.extend(colon(env, var, m))
			else:
				raise NotImplementedError()
				ret.append("%s%s" % (var, meth))
		else:
			ret.extend(env[var])
	return ret

class c(waflib.Tools.c.c):
	run_str = '${CC} ${ARCH_ST:ARCH} ${CFLAGS} ${CPPFLAGS} ${FRAMEWORKPATH_ST:FRAMEWORKPATH} ${CPPPATH_ST:INCPATHS} ${DEFINES_ST:DEFINES} ${CC_SRC_F}${SRC} ${CC_TGT_F}${TGT} ${ORDERED_CFLAGS}'

class cprogram(waflib.Tools.c.cprogram):
	run_str = '${LINK_CC} ${LINKFLAGS} ${CCLNK_SRC_F}${SRC} ${CCLNK_TGT_F}${TGT[0].abspath()} ${RPATH_ST:RPATH} ${FRAMEWORKPATH_ST:FRAMEWORKPATH} ${FRAMEWORK_ST:FRAMEWORK} ${ARCH_ST:ARCH} ${STLIB_MARKER} ${STLIBPATH_ST:STLIBPATH} ${STLIB_ST:STLIB} ${SHLIB_MARKER} ${LIBPATH_ST:LIBPATH} ${LIB_ST:LIB} ${ORDERED_LINKFLAGS}'

class cshlib(cprogram, waflib.Tools.c.cprogram):
    pass

@feature("cprogram", "cshlib", "cstlib", "python")
@before_method("propagate_uselib_vars")
def apply_ordered_flags(self):
	link_flag_name_to_template = {
		"FRAMEWORK": "${FRAMEWORK_ST:%s}",
		"LIB": "${LIB_ST:%s}",
		"LIBPATH": "${LIBPATH_ST:%s}",
		"LINKFLAGS": "${%s}",
		"STLIB": "${STLIB_ST:%s}"
    }

	c_flag_name_to_template = {
		"ARCH": "${ARCH_ST:%s}",
		"CFLAGS": "${%s}",
		"CPPFLAGS": "${%s}",
		"FRAMEWORKPATH": "${FRAMEWORKPATH_ST:%s}",
		"CPPPATH": "${CPPPATH_ST:%s}",
		"DEFINES": "${DEFINES_ST:%s}",
		"INCLUDES": "${CPPPATH_ST:%s}",
	}

	# FIXME: use correct uselib_vars
	uselib_vars = set()
	if "cprogram" in self.features:
		uselib_vars |= ccroot.USELIB_VARS["cprogram"]
	if "cshlib" in self.features:
		uselib_vars |= ccroot.USELIB_VARS["cshlib"]
	#if "c" in self.features:
	#	uselib_vars |= ccroot.USELIB_VARS["c"]
	#if "pyext" in self.features:
	#	uselib_vars |= ccroot.USELIB_VARS["pyext"]
	env = self.env

	uselibs = self.to_list(getattr(self, 'uselib', []))
	ordered_link = []
	ordered_c = []

	to_remove = []

	for uselib in uselibs:
		for uselib_var in uselib_vars:
			key = uselib_var + '_' + uselib
			value = env[key]
			if value:
				to_remove.append(key)
				if uselib_var in link_flag_name_to_template:
					flag_template = link_flag_name_to_template[uselib_var]
					ordered_link.append(flag_template % key)
				elif uselib_var in c_flag_name_to_template:
					flag_template = c_flag_name_to_template[uselib_var]
					ordered_c.append(flag_template % key)
				else:
					raise NotImplementedError(uselib_var)
	ordered_linkflags = self.interpolate_flags(" ".join(ordered_link))
	env["ORDERED_LINKFLAGS"] = ordered_linkflags
	#ordered_cflags = self.interpolate_flags(" ".join(ordered_c))
	#env["ORDERED_CFLAGS"] = ordered_cflags

	for key in to_remove:
		del env[key]

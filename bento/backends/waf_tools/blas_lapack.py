"""Experimental ! This will very likely change"""
import collections
import sys

from bento.commands.options \
    import \
        Option
from bento.backends.waf_backend \
    import \
        WAF_TOOLDIR

import waflib

from waflib import Options

_PLATFORM_DEFAULT_ORDER = collections.defaultdict(
    lambda: ["atlas", "mkl", "openblas", "generic"])
_PLATFORM_DEFAULT_ORDER.update({
        "win32": ["mkl", "generic"],
        "darwin": ["accelerate", "generic"],
})

_CBLAS_TO_KWARGS = {
        "mkl": {"lib": "mkl_intel_c,mkl_intel_thread,mkl_core,libiomp5md".split(",")},
        "atlas": {"lib": ["cblas", "atlas"]},
        "accelerate": {"framework": ["Accelerate"]},
        "openblas": {"lib": ["openblas"]},
        "generic": {"lib": ["cblas"]},
}

_LAPACK_TO_KWARGS = {
        "mkl": {"lib": "mkl_lapack95,mkl_blas95,mkl_intel_c,mkl_intel_thread,mkl_core,libiomp5md".split(",")},
        "atlas": {"lib": ["lapack", "f77blas", "cblas", "atlas"]},
        "accelerate": {"framework": ["Accelerate"]},
        "openblas": {"lib": ["openblas"]},
        "generic": {"lib": ["lapack", "blas"]},
}

_BLAS_TO_KWARGS = {
        "mkl": {"lib": "mkl_blas95,mkl_intel_c,mkl_intel_thread,mkl_core,libiomp5md".split(",")},
        "atlas": {"lib": ["f77blas", "cblas", "atlas"]},
        "accelerate": {"framework": ["Accelerate"]},
        "openblas": {"lib": ["openblas"]},
        "generic": {"lib": ["blas"]},
}

def get_blas_lapack_order(context):
    o, a = context.options_context.parser.parse_args(context.command_argv)
    if o.blas_lapack_type == "default" or o.blas_lapack_type is None:
        order = _PLATFORM_DEFAULT_ORDER[sys.platform]
    else:
        order = [o.blas_lapack_type]

    return order

def check_cblas(context, optimized):
    conf = context.waf_context

    msg = "Checking for %s (CBLAS)" % optimized.upper()

    kwargs = dict(_CBLAS_TO_KWARGS[optimized])
    kwargs.update({"msg": msg, "uselib_store": "CBLAS"})

    try:
        conf.check_cc(**kwargs)
        conf.env.HAS_CBLAS = True
    except waflib.Errors.ConfigurationError:
        conf.env.HAS_CBLAS = False

def check_blas(context, optimized):
    conf = context.waf_context

    msg = "Checking for %s (BLAS)" % optimized.upper()

    kwargs = _BLAS_TO_KWARGS[optimized]
    kwargs.update({"msg": msg, "uselib_store": "BLAS"})

    try:
        conf.check_cc(**kwargs)
        conf.env.HAS_BLAS = True
    except waflib.Errors.ConfigurationError:
        conf.env.HAS_BLAS = False

def check_lapack(context, optimized):
    conf = context.waf_context

    msg = "Checking for %s (LAPACK)" % optimized.upper()
    if optimized in ["openblas", "atlas"]:
        check_fortran(context)

    kwargs = dict(_LAPACK_TO_KWARGS[optimized])
    kwargs.update({"msg": msg, "uselib_store": "LAPACK"})

    try:
        conf.check_cc(**kwargs)
        conf.env.HAS_LAPACK = True
    except waflib.Errors.ConfigurationError:
        conf.env.HAS_LAPACK = False

def check_blas_lapack(context):
    conf = context.waf_context

    order = list(get_blas_lapack_order(context))

    o, a = context.options_context.parser.parse_args(context.command_argv)
    if o.blas_lapack_libdir:
        context.waf_context.env.append_value("LIBPATH", o.blas_lapack_libdir)

    for blas_lapack_name in order:
        check_cblas(context, blas_lapack_name)
        if conf.env.HAS_CBLAS:
            # prefer this source also for LAPACK
            order.remove(blas_lapack_name)
            order.insert(0, blas_lapack_name)
            break

    for blas_lapack_name in order:
        check_blas(context, blas_lapack_name)
        if conf.env.HAS_BLAS:
            break

    for blas_lapack_name in order:
        check_lapack(context, blas_lapack_name)
        if conf.env.HAS_LAPACK:
            break

    # You can manually set up blas/lapack as follows:
    #conf.env.HAS_CBLAS = True
    #conf.env.LIB_CBLAS = ["cblas", "atlas"]
    #conf.env.HAS_LAPACK = True
    #conf.env.LIB_LAPACK = ["lapack", "f77blas", "cblas", "atlas"]

def check_fortran(context):
    opts = context.waf_options_context
    conf = context.waf_context

    opts.load("compiler_fc")
    Options.options.check_fc = "gfortran"

    conf.load("compiler_fc")
    conf.load("ordered_c", tooldir=[WAF_TOOLDIR])

    conf.check_fortran_verbose_flag()
    conf.check_fortran_clib()

def add_options(global_context):
    global_context.add_option_group("configure", "blas_lapack", "blas/lapack")

    available_optimized = ",".join(_LAPACK_TO_KWARGS.keys())
    global_context.add_option("configure",
            Option("--blas-lapack-type", help="Which blas lapack to use (%s)" % available_optimized),
            "blas_lapack")

    global_context.add_option("configure",
            Option("--with-blas-lapack-libdir", dest="blas_lapack_libdir",
                   help="Where to look for BLAS/LAPACK dir"),
            "blas_lapack")

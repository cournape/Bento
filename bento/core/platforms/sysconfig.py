import os
import sys

import bento.utils.path

def get_scheme(platform):
    # Whenever you add a variable in schemes, you should add one in
    # scheme_opts as well, otherwise the it will not be customizable from
    # configure.
    schemes = {
        'unix': {
            'destdir': bento.utils.path.find_root(sys.prefix),
            'prefix': sys.prefix,
            'eprefix': sys.exec_prefix,
            'bindir': '$eprefix/bin',
            'sbindir': '$eprefix/sbin',
            'libexecdir': '$eprefix/libexec',
            'sysconfdir': '$prefix/etc',
            'sharedstatedir': '$prefix/com',
            'localstatedir': '$prefix/var',
            'libdir': '$eprefix/lib',
            'includedir': '$prefix/include',
            'datarootdir': '$prefix/share',
            'datadir': '$datarootdir',
            'mandir': '$datarootdir/man',
            'infodir': '$datarootdir/info',
            'localedir': '$datarootdir/locale',
            'docdir': '$datarootdir/doc/$pkgname',
            'htmldir': '$docdir',
            'dvidir': '$docdir',
            'psdir': '$docdir',
            'pdfdir': '$docdir',
            'sitedir': '$libdir/python$py_version_short/site-packages',
            'pkgdatadir': '$datadir/$pkgname'
        },
        'win32': {
            'destdir': bento.utils.path.find_root(sys.prefix),
            'prefix': sys.prefix,
            'eprefix': r'$prefix',
            'bindir': r'$eprefix\Scripts',
            'sbindir': r'$eprefix\Scripts',
            'libexecdir': r'$eprefix\Scripts',
            'sysconfdir': r'$prefix\etc',
            'sharedstatedir': r'$prefix\com',
            'localstatedir': r'$prefix\var',
            'libdir': r'$eprefix\lib',
            'includedir': r'$prefix\include',
            'datarootdir': r'$prefix\share',
            'datadir': r'$datarootdir',
            'mandir': r'$datarootdir\man',
            'infodir': r'$datarootdir\info',
            'localedir': r'$datarootdir\locale',
            'docdir': r'$datarootdir\doc\$pkgname',
            'htmldir': r'$docdir',
            'dvidir': r'$docdir',
            'psdir': r'$docdir',
            'pdfdir': r'$docdir',
            'sitedir': r'$prefix\Lib\site-packages',
            'pkgdatadir': r'$datadir\$pkgname'
        }
    }

    schemes_opts = {
        'prefix': {'opts': ['--prefix'],
                   'help': 'install architecture-independent files '
                           'in PREFIX [%s]'},
        'eprefix': {'opts': ['--exec-prefix'],
                   'help': 'install architecture-dependent files '
                           'in EPREFIX [%s]',
                    'dest': 'eprefix'},
        'bindir': {'opts': ['--bindir'],
                   'help': 'user executables [%s]'},
        'sbindir': {'opts': ['--sbindir'],
                   'help': 'system admin executables [%s]'},
        'libexecdir': {'opts': ['--libexecdir'],
                       'help': 'program executables [%s]'},
        'sysconfdir': {'opts': ['--sysconfdir'],
                       'help': 'read-only single-machine data [%s]'},
        'sharedstatedir': {'opts': ['--sharedstatedir'],
                           'help': 'modifiable architecture-independent data [%s]'},
        'localstatedir': {'opts': ['--localstatedir'],
                          'help': 'modifiable single-machine data [%s]'},
        'libdir': {'opts': ['--libdir'],
                   'help': 'object code library [%s]'},
        'includedir': {'opts': ['--includedir'],
                   'help': 'C header files [%s]'},
        'datarootdir': {'opts': ['--datarootdir'],
                   'help': 'read-only arch.-independent data root [%s]'},
        'datadir': {'opts': ['--datadir'],
                   'help': 'read-only arch.-independent data [%s]'},
        'infodir': {'opts': ['--infodir'],
                   'help': 'info documentation [%s]'},
        'localedir': {'opts': ['--localedir'],
                   'help': 'locale-dependent files [%s]'},
        'mandir': {'opts': ['--mandir'],
                   'help': 'man documentation [%s]'},
        'docdir': {'opts': ['--docdir'],
                   'help': 'documentation root [%s]'},
        'htmldir': {'opts': ['--htmldir'],
                   'help': 'html documentation [%s]'},
        'dvidir': {'opts': ['--dvidir'],
                   'help': 'dvi documentation [%s]'},
        'psdir': {'opts': ['--psdir'],
                   'help': 'ps documentation [%s]'},
        'pdfdir': {'opts': ['--pdfdir'],
                   'help': 'pdf documentation [%s]'},
        'sitedir': {'opts': ['--sitedir'],
                    'help': 'python site-packages [%s]'},
        'pkgdatadir': {'opts': ['--pkgdatadir'],
                    'help': 'package-specific data dir [%s]'},
        'destdir': {'opts': ['--destdir'],
                    'help': 'alternate root to install to [%s]'}
    }
    if platform.startswith('win32'):
        pkg_platform = platform
    else:
        pkg_platform = 'unix'

    try:
        scheme = schemes[pkg_platform]
    except KeyError:
        raise ValueError("Platform %s not yet supported" % platform)

    scheme_opts = {}
    for k, v in schemes_opts.items():
        val = schemes_opts[k].copy()
        val['help'] = val['help'] % scheme[k]
        scheme_opts[k] = val

    return scheme, scheme_opts

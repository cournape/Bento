import os
import sys
import subprocess

import six

import plistlib

from bento.compat.api \
    import \
        check_call

BENTO_INFO = "0.0.5"

MKBOM = "/usr/bin/mkbom"

def _unicode(*args, **kw):
    if six.PY3:
        return str(*args, **kw)
    else:
        return unicode(*args, **kw)

def path_requirement(SpecArgument, Level=six.u('requires'), **kw):
    return dict(
        Level=Level,
        SpecType=six.u('file'),
        SpecArgument=unicode_path(SpecArgument),
        SpecProperty=six.u('NSFileType'),
        TestOperator=six.u('eq'),
        TestObject=six.u('NSFileTypeDirectory'),
        **kw
    )

def common_info(pkg_info):
    # Keys that can appear in any package
    name = _unicode(pkg_info.name)
    major, minor = pkg_info.version_info[0], pkg_info.version_info[1]
    version = pkg_info.version
    defaults = dict(
        CFBundleGetInfoString='%s %s' % (name, version),
        CFBundleIdentifier='org.pythonmac.%s' % (name,),
        CFBundleName=name,
        CFBundleShortVersionString=_unicode(version),
        IFMajorVersion=major,
        IFMinorRevision=minor,
        IFPkgFormatVersion=0.10000000149011612,
        IFRequirementDicts=[path_requirement(six.u('/'))],
        PythonInfoDict=dict(
            PythonLongVersion=_unicode(sys.version),
            PythonShortVersion=_unicode(sys.version[:3]),
            PythonExecutable=_unicode(sys.executable),
            bento_version=dict(
                version=BENTO_INFO
            ),
        ),
    )
    return defaults

def common_description(pkg_info):
    return dict(
        IFPkgDescriptionTitle=_unicode(pkg_info.name),
        IFPkgDescriptionVersion=_unicode(pkg_info.version),
    )

def unicode_path(path, encoding=sys.getfilesystemencoding()):
    if isinstance(path, six.text_type):
        return path
    return _unicode(path, encoding)

def write(dct, path):
    p = plistlib.Plist()
    p.update(dct)
    p.write(path)

def ensure_directories(pkg_info):
    for d in [pkg_info.contents, pkg_info.resources, pkg_info.en_lproj]:
        if not os.path.exists(d):
            os.makedirs(d)

def build_bom(pkg_info):
    check_call([MKBOM, pkg_info.source_root, pkg_info.bom])

def build_archive(pkg_info):
    check_call(["pax", "-w", "-f", pkg_info.archive, "-x", "cpio", "-z", "."],
                          cwd=pkg_info.source_root)

def build_info_plist(pkg_info):
    d = common_info(pkg_info)

    # Keys that can only appear in single packages
    d.update(dict(
        IFPkgFlagAllowBackRev=False,
        IFPkgFlagAuthorizationAction=six.u('AdminAuthorization'),
        IFPkgFlagFollowLinks=True,
        IFPkgFlagInstallFat=False,
        IFPkgFlagIsRequired=False,
        IFPkgFlagOverwritePermissions=False,
        IFPkgFlagRelocatable=False,
        IFPkgFlagRestartAction=six.u('NoRestart'),
        IFPkgFlagRootVolumeOnly=True,
        IFPkgFlagUpdateInstalledLangauges=False,
    ))

    d.update(dict(
        IFPkgFlagAuthorizationAction=pkg_info.auth,
        IFPkgFlagDefaultLocation=unicode_path(pkg_info.prefix),
    ))
    write(d, pkg_info.info_plist)

def build_pkg_info(pkg_info):
    fid = open(pkg_info.pkg_info, "w")
    try:
        fid.write("pmkrpkg1")
    finally:
        fid.close()

def build_description_plist(pkg_info):
    desc = common_description(pkg_info)
    desc['IFPkgDescriptionDescription'] = pkg_info.description
    write(desc, pkg_info.description_plist)

def build_pkg(pkg_info):
    ensure_directories(pkg_info)

    build_bom(pkg_info)
    build_archive(pkg_info)

    build_info_plist(pkg_info)

    build_pkg_info(pkg_info)

    build_description_plist(pkg_info)

class PackageInfo(object):
    def __init__(self, pkg_name, prefix, source_root, pkg_root, admin=True, description=None, version=None):
        if admin:
            self.auth = six.u("AdminAuthorization")
        else:
            self.auth = six.u("RootAuthorization")

        # Where things will be installed by Mac OS X installer
        self.prefix = prefix
        # Root directory for files to be packaged
        self.source_root = source_root
        # Root directory for produced .pkg directory/file
        self.pkg_root = pkg_root

        self.name = pkg_name
        # FIXME: version handling -> use distutils2 version module
        self.version_info = (0, 0, 5, None)
        if version is None:
            self.version = ""
        else:
            self.version = version

        if description:
            self.description = description
        else:
            self.description = ""

        self.contents = os.path.join(self.pkg_root, "Contents")
        self.resources = os.path.join(self.contents, "Resources")
        self.en_lproj = os.path.join(self.resources, "en.lproj")

        self.bom = os.path.join(self.contents, "Archive.bom")
        self.archive = os.path.join(self.contents, "Archive.pax.gz")
        self.info_plist = os.path.join(self.contents, "Info.plist")
        self.pkg_info = os.path.join(self.contents, "PkgInfo")

        self.description_plist = os.path.join(self.en_lproj, "Description.plist")

class MetaPackageInfo(object):
    @classmethod
    def from_build_manifest(cls, build_manifest):
        m = build_manifest.meta
        info_string = "%s %s" % (m["name"], m["version"])
        identifier = "com.github.cournape.bento"
        version_info = (0, 0, 5)
        return cls(m["name"], info_string, version_info, identifier, m["summary"])

    def __init__(self, name, info_string, version_info, identifier, summary):
        self.major, self.minor, self.micro = version_info[0], version_info[1], version_info[2]

        self.info_string = info_string
        self.name = name
        self.identifier = identifier
        self.description = summary

        self.short_version = ".".join([str(i) for i in [self.major, self.minor, self.micro]])

def make_mpkg_plist(mpkg_info, path):
    pl = dict(
            CFBundleGetInfoString=mpkg_info.info_string,
            CFBundleIdentifier=mpkg_info.identifier,
            CFBundleName=mpkg_info.name,
            CFBundleShortVersionString=mpkg_info.short_version,
            IFMajorVersion=mpkg_info.major,
            IFMinorVersion=mpkg_info.minor,
            IFPkgFlagComponentDirectory="Contents/Packages",
            IFPkgFlagPackageList=[
                dict(
                    IFPkgFlagPackageLocation=pkg,
                    IFPkgFlagPackageSelection='selected'
                )
                for pkg in mpkg_info.packages
            ],
            IFPkgFormatVersion=0.10000000149011612,
            IFPkgFlagBackgroundScaling="proportional",
            IFPkgFlagBackgroundAlignment="left",
            IFPkgFlagAuthorizationAction="RootAuthorization",
        )

    write(pl, path)
    return pl

def make_mpkg_description(mpkg_info, path):
    d = dict(IFPkgDescriptionTitle=mpkg_info.name,
             IFPkgDescriptionDescription=mpkg_info.description,
             IFPkgDescriptionVersion=mpkg_info.short_version)
    write(d, path)

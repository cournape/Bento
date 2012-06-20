import os
import msilib

from distutils import sysconfig
from msilib import schema, sequence, add_data, text

from msilib \
    import \
        Dialog, Directory, Feature

from bento.core.meta \
    import \
        PackageMetadata

ALL_VERSIONS = ['2.0', '2.1', '2.2', '2.3', '2.4',
                '2.5', '2.6', '2.7', '2.8', '2.9',
                '3.0', '3.1', '3.2', '3.3', '3.4',
                '3.5', '3.6', '3.7', '3.8', '3.9']
OTHER_VERSION = 'X'

class PyDialog(Dialog):
    """Dialog class with a fixed layout: controls at the top, then a ruler,
    then a list of buttons: back, next, cancel. Optionally a bitmap at the
    left."""
    def __init__(self, *args, **kw):
        """Dialog(database, name, x, y, w, h, attributes, title, first,
        default, cancel, bitmap=true)"""
        Dialog.__init__(self, *args)
        ruler = self.h - 36
        #if kw.get("bitmap", True):
        #    self.bitmap("Bitmap", 0, 0, bmwidth, ruler, "PythonWin")
        self.line("BottomLine", 0, ruler, self.w, 0)

    def title(self, title):
        "Set the title text of the dialog at the top."
        # name, x, y, w, h, flags=Visible|Enabled|Transparent|NoPrefix,
        # text, in VerdanaBold10
        self.text("Title", 15, 10, 320, 60, 0x30003,
                  r"{\VerdanaBold10}%s" % title)

    def back(self, title, next, name = "Back", active = 1):
        """Add a back button with a given title, the tab-next button,
        its name in the Control table, possibly initially disabled.

        Return the button, so that events can be associated"""
        if active:
            flags = 3 # Visible|Enabled
        else:
            flags = 1 # Visible
        return self.pushbutton(name, 180, self.h-27 , 56, 17, flags, title, next)

    def cancel(self, title, next, name = "Cancel", active = 1):
        """Add a cancel button with a given title, the tab-next button,
        its name in the Control table, possibly initially disabled.

        Return the button, so that events can be associated"""
        if active:
            flags = 3 # Visible|Enabled
        else:
            flags = 1 # Visible
        return self.pushbutton(name, 304, self.h-27, 56, 17, flags, title, next)

    def next(self, title, next, name = "Next", active = 1):
        """Add a Next button with a given title, the tab-next button,
        its name in the Control table, possibly initially disabled.

        Return the button, so that events can be associated"""
        if active:
            flags = 3 # Visible|Enabled
        else:
            flags = 1 # Visible
        return self.pushbutton(name, 236, self.h-27, 56, 17, flags, title, next)

    def xbutton(self, name, title, next, xpos):
        """Add a button with a given title, the tab-next button,
        its name in the Control table, giving its x position; the
        y-position is aligned with the other buttons.

        Return the button, so that events can be associated"""
        return self.pushbutton(name, int(self.w*xpos - 28), self.h-27, 56, 17, 3, title, next)

def add_find_python(db, versions):
    """Adds code to the installer to compute the location of Python.

    Properties PYTHON.MACHINE.X.Y and PYTHON.USER.X.Y will be set from the
    registry for each version of Python.

    Properties TARGETDIRX.Y will be set from PYTHON.USER.X.Y if defined,
    else from PYTHON.MACHINE.X.Y.

    Properties PYTHONX.Y will be set to TARGETDIRX.Y\\python.exe"""

    start = 402
    for ver in versions:
        install_path = r"SOFTWARE\Python\PythonCore\%s\InstallPath" % ver
        machine_reg = "python.machine." + ver
        user_reg = "python.user." + ver
        machine_prop = "PYTHON.MACHINE." + ver
        user_prop = "PYTHON.USER." + ver
        machine_action = "PythonFromMachine" + ver
        user_action = "PythonFromUser" + ver
        exe_action = "PythonExe" + ver
        target_dir_prop = "TARGETDIR" + ver
        exe_prop = "PYTHON" + ver
        if msilib.Win64:
            # type: msidbLocatorTypeRawValue + msidbLocatorType64bit
            Type = 2+16
        else:
            Type = 2
        add_data(db, "RegLocator",
                [(machine_reg, 2, install_path, None, Type),
                 (user_reg, 1, install_path, None, Type)])
        add_data(db, "AppSearch",
                [(machine_prop, machine_reg),
                 (user_prop, user_reg)])
        add_data(db, "CustomAction",
                [(machine_action, 51+256, target_dir_prop, "[" + machine_prop + "]"),
                 (user_action, 51+256, target_dir_prop, "[" + user_prop + "]"),
                 (exe_action, 51+256, exe_prop, "[" + target_dir_prop + "]\\python.exe"),
                ])
        add_data(db, "InstallExecuteSequence",
                [(machine_action, machine_prop, start),
                 (user_action, user_prop, start + 1),
                 (exe_action, None, start + 2),
                ])
        add_data(db, "InstallUISequence",
                [(machine_action, machine_prop, start),
                 (user_action, user_prop, start + 1),
                 (exe_action, None, start + 2),
                ])
        add_data(db, "Condition",
                [("Python" + ver, 0, "NOT TARGETDIR" + ver)])
        start += 4
        assert start < 500

def add_files(db, msi_node, versions, other_version, install_script=None):
    if install_script is not None:
        raise NotImplementedError("Support for msi install script not yet implemented")
    cab = msilib.CAB("distfiles")
    rootdir = msi_node.abspath()

    root = Directory(db, cab, None, rootdir, "TARGETDIR", "SourceDir")
    f = Feature(db, "Python", "Python", "Everything",
                0, 1, directory="TARGETDIR")

    items = [(f, root, '')]
    for version in versions + [other_version]:
        target = "TARGETDIR" + version
        name = default = "Python" + version
        desc = "Everything"
        if version is other_version:
            title = "Python from another location"
            level = 2
        else:
            title = "Python %s from registry" % version
            level = 1
        f = Feature(db, name, title, desc, 1, level, directory=target)
        dir = Directory(db, cab, root, rootdir, target, default)
        items.append((f, dir, version))
    db.Commit()

    seen = {}
    for feature, dir, version in items:
        todo = [dir]
        while todo:
            dir = todo.pop()
            for file in os.listdir(dir.absolute):
                afile = os.path.join(dir.absolute, file)
                if os.path.isdir(afile):
                    short = "%s|%s" % (dir.make_short(file), file)
                    default = file + version
                    newdir = Directory(db, cab, dir, file, default, short)
                    todo.append(newdir)
                else:
                    if not dir.component:
                        dir.start_component(dir.logical, feature, 0)
                    if afile not in seen:
                        key = seen[afile] = dir.add_file(file)
                        if file==install_script:
                            if install_script_key:
                                raise DistutilsOptionError(
                                      "Multiple files with name %s" % file)
                            install_script_key = '[#%s]' % key
                    else:
                        key = seen[afile]
                        add_data(db, "DuplicateFile",
                            [(key + version, dir.component, key, None, dir.logical)])
        db.Commit()
    cab.commit(db)

def add_scripts(db, install_scripts=None, pre_install_scripts=None):
    if install_scripts:
        raise NotImplementedError("install scripts not yet supported")

    if pre_install_scripts:
        raise NotImplementedError("pre install scripts not yet supported")

def add_ui(db, fullname, versions, other_version):
    x = y = 50
    w = 370
    h = 300
    title = "[ProductName] Setup"

    # see "Dialog Style Bits"
    modal = 3      # visible | modal
    modeless = 1   # visible

    # UI customization properties
    add_data(db, "Property",
             # See "DefaultUIFont Property"
             [("DefaultUIFont", "DlgFont8"),
              # See "ErrorDialog Style Bit"
              ("ErrorDialog", "ErrorDlg"),
              ("Progress1", "Install"),   # modified in maintenance type dlg
              ("Progress2", "installs"),
              ("MaintenanceForm_Action", "Repair"),
              # possible values: ALL, JUSTME
              ("WhichUsers", "ALL")
             ])

    # Fonts, see "TextStyle Table"
    add_data(db, "TextStyle",
             [("DlgFont8", "Tahoma", 9, None, 0),
              ("DlgFontBold8", "Tahoma", 8, None, 1), #bold
              ("VerdanaBold10", "Verdana", 10, None, 1),
              ("VerdanaRed9", "Verdana", 9, 255, 0),
             ])

    # UI Sequences, see "InstallUISequence Table", "Using a Sequence Table"
    # Numbers indicate sequence; see sequence.py for how these action integrate
    add_data(db, "InstallUISequence",
             [("PrepareDlg", "Not Privileged or Windows9x or Installed", 140),
              ("WhichUsersDlg", "Privileged and not Windows9x and not Installed", 141),
              # In the user interface, assume all-users installation if privileged.
              ("SelectFeaturesDlg", "Not Installed", 1230),
              # XXX no support for resume installations yet
              #("ResumeDlg", "Installed AND (RESUME OR Preselected)", 1240),
              ("MaintenanceTypeDlg", "Installed AND NOT RESUME AND NOT Preselected", 1250),
              ("ProgressDlg", None, 1280)])

    add_data(db, 'ActionText', text.ActionText)
    add_data(db, 'UIText', text.UIText)
    #####################################################################
    # Standard dialogs: FatalError, UserExit, ExitDialog
    fatal=PyDialog(db, "FatalError", x, y, w, h, modal, title,
                 "Finish", "Finish", "Finish")
    fatal.title("[ProductName] Installer ended prematurely")
    fatal.back("< Back", "Finish", active = 0)
    fatal.cancel("Cancel", "Back", active = 0)
    fatal.text("Description1", 15, 70, 320, 80, 0x30003,
               "[ProductName] setup ended prematurely because of an error.  Your system has not been modified.  To install this program at a later time, please run the installation again.")
    fatal.text("Description2", 15, 155, 320, 20, 0x30003,
               "Click the Finish button to exit the Installer.")
    c=fatal.next("Finish", "Cancel", name="Finish")
    c.event("EndDialog", "Exit")

    user_exit = PyDialog(db, "UserExit", x, y, w, h, modal, title,
                 "Finish", "Finish", "Finish")
    user_exit.title("[ProductName] Installer was interrupted")
    user_exit.back("< Back", "Finish", active = 0)
    user_exit.cancel("Cancel", "Back", active = 0)
    user_exit.text("Description1", 15, 70, 320, 80, 0x30003,
               "[ProductName] setup was interrupted.  Your system has not been modified.  "
               "To install this program at a later time, please run the installation again.")
    user_exit.text("Description2", 15, 155, 320, 20, 0x30003,
               "Click the Finish button to exit the Installer.")
    c = user_exit.next("Finish", "Cancel", name="Finish")
    c.event("EndDialog", "Exit")

    exit_dialog = PyDialog(db, "ExitDialog", x, y, w, h, modal, title,
                         "Finish", "Finish", "Finish")
    exit_dialog.title("Completing the [ProductName] Installer")
    exit_dialog.back("< Back", "Finish", active = 0)
    exit_dialog.cancel("Cancel", "Back", active = 0)
    exit_dialog.text("Description", 15, 235, 320, 20, 0x30003,
               "Click the Finish button to exit the Installer.")
    c = exit_dialog.next("Finish", "Cancel", name="Finish")
    c.event("EndDialog", "Return")

    #####################################################################
    # Required dialog: FilesInUse, ErrorDlg
    inuse = PyDialog(db, "FilesInUse",
                     x, y, w, h,
                     19,                # KeepModeless|Modal|Visible
                     title,
                     "Retry", "Retry", "Retry", bitmap=False)
    inuse.text("Title", 15, 6, 200, 15, 0x30003,
               r"{\DlgFontBold8}Files in Use")
    inuse.text("Description", 20, 23, 280, 20, 0x30003,
           "Some files that need to be updated are currently in use.")
    inuse.text("Text", 20, 55, 330, 50, 3,
               "The following applications are using files that need to be updated by this setup. Close these applications and then click Retry to continue the installation or Cancel to exit it.")
    inuse.control("List", "ListBox", 20, 107, 330, 130, 7, "FileInUseProcess",
                  None, None, None)
    c=inuse.back("Exit", "Ignore", name="Exit")
    c.event("EndDialog", "Exit")
    c=inuse.next("Ignore", "Retry", name="Ignore")
    c.event("EndDialog", "Ignore")
    c=inuse.cancel("Retry", "Exit", name="Retry")
    c.event("EndDialog","Retry")

    # See "Error Dialog". See "ICE20" for the required names of the controls.
    error = Dialog(db, "ErrorDlg",
                   50, 10, 330, 101,
                   65543,       # Error|Minimize|Modal|Visible
                   title,
                   "ErrorText", None, None)
    error.text("ErrorText", 50,9,280,48,3, "")
    #error.control("ErrorIcon", "Icon", 15, 9, 24, 24, 5242881, None, "py.ico", None, None)
    error.pushbutton("N",120,72,81,21,3,"No",None).event("EndDialog","ErrorNo")
    error.pushbutton("Y",240,72,81,21,3,"Yes",None).event("EndDialog","ErrorYes")
    error.pushbutton("A",0,72,81,21,3,"Abort",None).event("EndDialog","ErrorAbort")
    error.pushbutton("C",42,72,81,21,3,"Cancel",None).event("EndDialog","ErrorCancel")
    error.pushbutton("I",81,72,81,21,3,"Ignore",None).event("EndDialog","ErrorIgnore")
    error.pushbutton("O",159,72,81,21,3,"Ok",None).event("EndDialog","ErrorOk")
    error.pushbutton("R",198,72,81,21,3,"Retry",None).event("EndDialog","ErrorRetry")

    #####################################################################
    # Global "Query Cancel" dialog
    cancel = Dialog(db, "CancelDlg", 50, 10, 260, 85, 3, title,
                    "No", "No", "No")
    cancel.text("Text", 48, 15, 194, 30, 3,
                "Are you sure you want to cancel [ProductName] installation?")
    #cancel.control("Icon", "Icon", 15, 15, 24, 24, 5242881, None,
    #               "py.ico", None, None)
    c=cancel.pushbutton("Yes", 72, 57, 56, 17, 3, "Yes", "No")
    c.event("EndDialog", "Exit")

    c=cancel.pushbutton("No", 132, 57, 56, 17, 3, "No", "Yes")
    c.event("EndDialog", "Return")

    #####################################################################
    # Global "Wait for costing" dialog
    costing = Dialog(db, "WaitForCostingDlg", 50, 10, 260, 85, modal, title,
                     "Return", "Return", "Return")
    costing.text("Text", 48, 15, 194, 30, 3,
                 "Please wait while the installer finishes determining your disk space requirements.")
    c = costing.pushbutton("Return", 102, 57, 56, 17, 3, "Return", None)
    c.event("EndDialog", "Exit")

    #####################################################################
    # Preparation dialog: no user input except cancellation
    prep = PyDialog(db, "PrepareDlg", x, y, w, h, modeless, title,
                    "Cancel", "Cancel", "Cancel")
    prep.text("Description", 15, 70, 320, 40, 0x30003,
              "Please wait while the Installer prepares to guide you through the installation.")
    prep.title("Welcome to the [ProductName] Installer")
    c=prep.text("ActionText", 15, 110, 320, 20, 0x30003, "Pondering...")
    c.mapping("ActionText", "Text")
    c=prep.text("ActionData", 15, 135, 320, 30, 0x30003, None)
    c.mapping("ActionData", "Text")
    prep.back("Back", None, active=0)
    prep.next("Next", None, active=0)
    c=prep.cancel("Cancel", None)
    c.event("SpawnDialog", "CancelDlg")

    #####################################################################
    # Feature (Python directory) selection
    seldlg = PyDialog(db, "SelectFeaturesDlg", x, y, w, h, modal, title,
                    "Next", "Next", "Cancel")
    seldlg.title("Select Python Installations")

    seldlg.text("Hint", 15, 30, 300, 20, 3,
                "Select the Python locations where %s should be installed."
                % fullname)

    seldlg.back("< Back", None, active=0)
    c = seldlg.next("Next >", "Cancel")
    order = 1
    c.event("[TARGETDIR]", "[SourceDir]", ordering=order)
    for version in versions + [other_version]:
        order += 1
        c.event("[TARGETDIR]", "[TARGETDIR%s]" % version,
                "FEATURE_SELECTED AND &Python%s=3" % version,
                ordering=order)
    c.event("SpawnWaitDialog", "WaitForCostingDlg", ordering=order + 1)
    c.event("EndDialog", "Return", ordering=order + 2)
    c = seldlg.cancel("Cancel", "Features")
    c.event("SpawnDialog", "CancelDlg")

    c = seldlg.control("Features", "SelectionTree", 15, 60, 300, 120, 3,
                       "FEATURE", None, "PathEdit", None)
    c.event("[FEATURE_SELECTED]", "1")
    ver = other_version
    install_other_cond = "FEATURE_SELECTED AND &Python%s=3" % ver
    dont_install_other_cond = "FEATURE_SELECTED AND &Python%s<>3" % ver

    c = seldlg.text("Other", 15, 200, 300, 15, 3,
                    "Provide an alternate Python location")
    c.condition("Enable", install_other_cond)
    c.condition("Show", install_other_cond)
    c.condition("Disable", dont_install_other_cond)
    c.condition("Hide", dont_install_other_cond)

    c = seldlg.control("PathEdit", "PathEdit", 15, 215, 300, 16, 1,
                       "TARGETDIR" + ver, None, "Next", None)
    c.condition("Enable", install_other_cond)
    c.condition("Show", install_other_cond)
    c.condition("Disable", dont_install_other_cond)
    c.condition("Hide", dont_install_other_cond)

    #####################################################################
    # Disk cost
    cost = PyDialog(db, "DiskCostDlg", x, y, w, h, modal, title,
                    "OK", "OK", "OK", bitmap=False)
    cost.text("Title", 15, 6, 200, 15, 0x30003,
              "{\DlgFontBold8}Disk Space Requirements")
    cost.text("Description", 20, 20, 280, 20, 0x30003,
              "The disk space required for the installation of the selected features.")
    cost.text("Text", 20, 53, 330, 60, 3,
              "The highlighted volumes (if any) do not have enough disk space "
          "available for the currently selected features.  You can either "
          "remove some files from the highlighted volumes, or choose to "
          "install less features onto local drive(s), or select different "
          "destination drive(s).")
    cost.control("VolumeList", "VolumeCostList", 20, 100, 330, 150, 393223,
                 None, "{120}{70}{70}{70}{70}", None, None)
    cost.xbutton("OK", "Ok", None, 0.5).event("EndDialog", "Return")

    #####################################################################
    # WhichUsers Dialog. Only available on NT, and for privileged users.
    # This must be run before FindRelatedProducts, because that will
    # take into account whether the previous installation was per-user
    # or per-machine. We currently don't support going back to this
    # dialog after "Next" was selected; to support this, we would need to
    # find how to reset the ALLUSERS property, and how to re-run
    # FindRelatedProducts.
    # On Windows9x, the ALLUSERS property is ignored on the command line
    # and in the Property table, but installer fails according to the documentation
    # if a dialog attempts to set ALLUSERS.
    whichusers = PyDialog(db, "WhichUsersDlg", x, y, w, h, modal, title,
                        "AdminInstall", "Next", "Cancel")
    whichusers.title("Select whether to install [ProductName] for all users of this computer.")
    # A radio group with two options: allusers, justme
    g = whichusers.radiogroup("AdminInstall", 15, 60, 260, 50, 3,
                              "WhichUsers", "", "Next")
    g.add("ALL", 0, 5, 150, 20, "Install for all users")
    g.add("JUSTME", 0, 25, 150, 20, "Install just for me")

    whichusers.back("Back", None, active=0)

    c = whichusers.next("Next >", "Cancel")
    c.event("[ALLUSERS]", "1", 'WhichUsers="ALL"', 1)
    c.event("EndDialog", "Return", ordering = 2)

    c = whichusers.cancel("Cancel", "AdminInstall")
    c.event("SpawnDialog", "CancelDlg")

    #####################################################################
    # Installation Progress dialog (modeless)
    progress = PyDialog(db, "ProgressDlg", x, y, w, h, modeless, title,
                        "Cancel", "Cancel", "Cancel", bitmap=False)
    progress.text("Title", 20, 15, 200, 15, 0x30003,
                  "{\DlgFontBold8}[Progress1] [ProductName]")
    progress.text("Text", 35, 65, 300, 30, 3,
                  "Please wait while the Installer [Progress2] [ProductName]. "
                  "This may take several minutes.")
    progress.text("StatusLabel", 35, 100, 35, 20, 3, "Status:")

    c=progress.text("ActionText", 70, 100, w-70, 20, 3, "Pondering...")
    c.mapping("ActionText", "Text")

    #c=progress.text("ActionData", 35, 140, 300, 20, 3, None)
    #c.mapping("ActionData", "Text")

    c=progress.control("ProgressBar", "ProgressBar", 35, 120, 300, 10, 65537,
                       None, "Progress done", None, None)
    c.mapping("SetProgress", "Progress")

    progress.back("< Back", "Next", active=False)
    progress.next("Next >", "Cancel", active=False)
    progress.cancel("Cancel", "Back").event("SpawnDialog", "CancelDlg")

    ###################################################################
    # Maintenance type: repair/uninstall
    maint = PyDialog(db, "MaintenanceTypeDlg", x, y, w, h, modal, title,
                     "Next", "Next", "Cancel")
    maint.title("Welcome to the [ProductName] Setup Wizard")
    maint.text("BodyText", 15, 63, 330, 42, 3,
               "Select whether you want to repair or remove [ProductName].")
    g=maint.radiogroup("RepairRadioGroup", 15, 108, 330, 60, 3,
                        "MaintenanceForm_Action", "", "Next")
    #g.add("Change", 0, 0, 200, 17, "&Change [ProductName]")
    g.add("Repair", 0, 18, 200, 17, "&Repair [ProductName]")
    g.add("Remove", 0, 36, 200, 17, "Re&move [ProductName]")

    maint.back("< Back", None, active=False)
    c=maint.next("Finish", "Cancel")
    # Change installation: Change progress dialog to "Change", then ask
    # for feature selection
    #c.event("[Progress1]", "Change", 'MaintenanceForm_Action="Change"', 1)
    #c.event("[Progress2]", "changes", 'MaintenanceForm_Action="Change"', 2)

    # Reinstall: Change progress dialog to "Repair", then invoke reinstall
    # Also set list of reinstalled features to "ALL"
    c.event("[REINSTALL]", "ALL", 'MaintenanceForm_Action="Repair"', 5)
    c.event("[Progress1]", "Repairing", 'MaintenanceForm_Action="Repair"', 6)
    c.event("[Progress2]", "repairs", 'MaintenanceForm_Action="Repair"', 7)
    c.event("Reinstall", "ALL", 'MaintenanceForm_Action="Repair"', 8)

    # Uninstall: Change progress to "Remove", then invoke uninstall
    # Also set list of removed features to "ALL"
    c.event("[REMOVE]", "ALL", 'MaintenanceForm_Action="Remove"', 11)
    c.event("[Progress1]", "Removing", 'MaintenanceForm_Action="Remove"', 12)
    c.event("[Progress2]", "removes", 'MaintenanceForm_Action="Remove"', 13)
    c.event("Remove", "ALL", 'MaintenanceForm_Action="Remove"', 14)

    # Close dialog when maintenance action scheduled
    c.event("EndDialog", "Return", 'MaintenanceForm_Action<>"Change"', 20)
    #c.event("NewDialog", "SelectFeaturesDlg", 'MaintenanceForm_Action="Change"', 21)

    maint.cancel("Cancel", "RepairRadioGroup").event("SpawnDialog", "CancelDlg")

def create_msi_installer(package, run_node, msi_root_node, installer_name=None, output_dir="dist"):
    meta = PackageMetadata.from_package(package)

    string_version = "%d.%d.%d" % (meta.version_major, meta.version_minor, meta.version_micro)

    fullname = "%s-%s" % (package.name, string_version)
    if installer_name is None:
        installer_name = "%s-%s.msi" % (package.name, string_version)
    parent_node = run_node.make_node(output_dir)
    if parent_node is None:
        raise IOError()
    installer_node = parent_node.make_node(installer_name)
    installer_name = installer_node.abspath()
    installer_node.parent.mkdir()

    author = meta.author

    short_version = sysconfig.get_python_version()

    has_ext_modules = True
    if has_ext_modules:
        target_version = short_version
    else:
        target_version = None

    if target_version:
        product_name = "Python %s %s" % (target_version, meta.fullname)
    else:
        product_name = "Python %s" % meta.fullname

    if target_version:
        versions = [target_version]
    else:
        versions = list(ALL_VERSIONS)

    db = msilib.init_database(installer_name, schema, product_name, msilib.gen_uuid(), string_version, author)
    msilib.add_tables(db, sequence)

    props = [('DistVersion', meta.version)]
    email = meta.author_email or meta.maintainer_email
    if email:
        props.append(("ARPCONTACT", email))
    if meta.url:
        props.append(("ARPURLINFOABOUT", meta.url))
    if props:
        add_data(db, 'Property', props)

    add_find_python(db, versions)
    add_files(db, msi_root_node, versions, OTHER_VERSION)
    add_scripts(db)
    add_ui(db, fullname, versions, OTHER_VERSION)
    db.Commit()

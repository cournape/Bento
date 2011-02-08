"""Option handling module.

This module is concerned with options/argument parsing from both
bento and bento subcommands, as well as help message
formatting."""
import optparse

# Goal of separate options context:
#   - separate options handling from commands themselves (simplify commands)
#   - easier to add options from hook files
#   - should help hiding command implementation detail from hooks and high
#   level tools such as bentomaker (close coupling at the moment)
class OptionsContext(object):
    def __init__(self):
        self.parser = optparse.OptionParser(add_help_option=False)
        self._groups = {}
        self._is_setup = False

    def setup(self, package_options):
        self.add_group("build_customization", "Build customization")
        opt = optparse.Option("--use-distutils", help="Build extensions with distutils",
                              action="store_true")
        self.add_option(opt, "build_customization")

        self._is_setup = True

    def add_option(self, option, group=None):
        if group is None:
            self.parser.add_option(option)
        else:
            if group in self._groups:
                self._groups[group].add_option(option)
            else:
                raise ValueError("Unknown option group %r" % group)

    def add_group(self, name, title):
        grp = optparse.OptionGroup(self.parser, title)
        self._groups[name] = grp
        self.parser.add_option_group(grp)


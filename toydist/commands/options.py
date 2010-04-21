"""Option handling module.

This module is concerned with options/argument parsing from both
toydist and toydist subcommands, as well as help message
formatting."""
import optparse

from toydist.commands.errors \
    import \
        UsageException
from toydist.commands._config \
    import \
        SCRIPT_NAME

# What is required for command handling
# =====================================
#
# Command usage string
# --------------------
#
#    Purpose: one line
#    Usage: command subcommand ARG_TYPE
#
#    Options:
#      short,long  help
#
#    Description:
#      paragraph (in rest eventually)
#
#    See also
#
# Type of options
# ---------------
#
# What's needed:
#   - grouping options together
#   - general options vs command-specific options ?
#   - options common to every command
#   - arguments: necessary (with default ?) | optionals

class Option(object):
    def __init__(self, name, help='', tp=None, short_name=None):
        self.name = name
        self.help = help
        self.tp = tp
        self.short_name = short_name

    def is_flag(self):
        return self.tp is None

    def long_name_repr(self):
        return "--%s" % self.name

    def short_name_repr(self):
        if self.short_name:
            return "-%s" % self.short_name

    def shortest_repr(self):
        if self.short_name:
            return self.short_name_repr()
        return self.long_name_repr()

class Argument(object):
    """Command line argument representation."""
    @classmethod
    def from_string(cls, s):
        return cls(s[:-1], s[-1])

    def __init__(self, name, tp=None):
        self.name = name
        if tp is None or tp == "":
            self.tp = ""
        elif tp in ["?", "*"]:
            self.tp = tp
        else:
            raise ValueError("Gne ?")

    def is_optional(self):
        return self.tp in ["?", "*"]

class OptionParser(optparse.OptionParser):
    def __init__(self, description):
        optparse.OptionParser.__init__(self, description=description,
                add_help_option=False)
        self._opts = []

    def add_option(self, opt):
        self._opts.append(opt)
        optparse.OptionParser.add_option(self, opt)

    def error(self, msg):
        raise UsageException("%s: ERROR: %s" % (SCRIPT_NAME, msg))

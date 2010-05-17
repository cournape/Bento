import sys

def import_tools(tool_list, tooldirs=None):
    old_sys = sys.path[:]
    if tooldirs is not None:
        sys.path = tooldirs + sys.path

    try:
        for t in tool_list:
            __import__(t)
    finally:
        sys.path = old_sys

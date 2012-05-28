import os

import os.path as op


def find_root(p):
    """Return the 'root' of the given path.

    Example
    -------
    >>> find_root("/Users/joe")
    '/'
    """
    while p != op.dirname(p):
        p = op.dirname(p)
    return p

def ensure_dir(path):
    d = op.dirname(path)
    if d and not op.exists(d):
        os.makedirs(d)

def unnormalize_path(path):
    return path.replace("/", "\\")

def normalize_path(path):
    return path.replace("\\", "/")

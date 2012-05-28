from bento.utils.os2 \
    import \
        rename

def safe_write(target, writer, mode="wb"):
    """a 'safe' way to write to files.

    Instead of writing directly into a file, this function writes to a
    temporary file, and then rename the file to the target. On sane
    platforms, rename is atomic, so this avoids leaving stale
    files in inconsistent states.

    Parameters
    ----------
    target: str
        destination to write to
    writer: callable
        function which takes one argument, a file descriptor, and
        writes content to it
    mode: str
        opening mode
    """
    f = open(target + ".tmp", mode)
    try:
        writer(f)
    finally:
        f.close()
        rename(target + ".tmp", target)

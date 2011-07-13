__all__ = ["join_bytes"]

def join_bytes(seq):
    return b"".join(seq)

def function_code(f):
    return f.__code__

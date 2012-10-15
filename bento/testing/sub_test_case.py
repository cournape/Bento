import os
import sys
import subprocess
import copy

from bento.compat.api.moves \
    import \
        unittest

TEMPLATE = """\
import sys

from bento.compat.api.moves \
    import \
        unittest

from %(module_name)s import %(class_name)s

if __name__ == "__main__":
    result = unittest.TestResult()
    suite = unittest.TestSuite()
    suite.addTest(%(class_name)s("%(test_function)s"))
    suite.run(result)
    if len(result.errors) > 0:
        assert len(result.errors) == 1
        sys.stderr.write(result.errors[0][1])
        sys.exit(1)
    elif len(result.failures) > 0:
        assert len(result.failures) == 1
        sys.stderr.write(result.failures[0][1])
        sys.exit(2)
    else:
        sys.exit(0)
"""

def _execute_test(module_name, class_name, function_name):
    code = TEMPLATE % {"module_name": module_name, "class_name": class_name,
            "test_function": function_name}

    cmd = [sys.executable]

    if sys.platform == "win32":
        env = copy.deepcopy(os.environ)
    else:
        env = {"PYTHONPATH": os.environ.get("PYTHONPATH", "")}
    env["SUBTESTPIPE"] = "1"
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            stdin=subprocess.PIPE, env=env)
    out, err = p.communicate(code.encode())
    return out, err, p.returncode

class SubprocessTestCase(unittest.TestCase):
    """Simple unittest.TestCase subclass to execute every test in a different
    subprocess.
    
    Class-level tearDown and setUp are executed in the same subprocess as their
    corresponding test.
    """
    def run(self, result=None):
        is_sub = os.environ.get("SUBTESTPIPE", "0")
        if is_sub == "0":
            module_name = self.__module__
            class_name = self.__class__.__name__
            function_name = self._testMethodName
            result.startTest(self)
            try:
                out, err, st = _execute_test(module_name, class_name, function_name)
                out = out.decode()
                err = err.decode()
                sys.stdout.write(out)
                if st == 0:
                    result.addSuccess(self)
                elif st == 1:
                    result.errors.append([self, err])
                    sys.stderr.write("ERROR\n")
                elif st == 2:
                    result.failures.append([self, err])
                    sys.stderr.write("FAILED\n")
                else:
                    raise ValueError("Unexpected subprocess test failure")
            finally:
                result.stopTest(self)
        else:
            return super(SubprocessTestCase, self).run(result)

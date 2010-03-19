import shutil
import os
import sys

from subprocess import *
from copy import copy

from os.path import join as pjoin

VENV_DIR = os.path.abspath("test_env")

if os.path.exists(VENV_DIR):
    shutil.rmtree(VENV_DIR)
if os.path.exists("build"):
    shutil.rmtree("build")

pid = Popen(["virtualenv", VENV_DIR], stdout=PIPE, stderr=STDOUT)
stdout = pid.communicate()[0]
assert pid.returncode == 0

def call_venv(cmd, cwd=None):
    env = copy(os.environ)
    if sys.platform == "win32":
        raise ValueError()
    else:
        env["PATH"] = pjoin(VENV_DIR, "bin") + os.pathsep + env["PATH"]
    pid = Popen(cmd, stdout=PIPE, stderr=STDOUT, env=env, cwd=cwd)
    stdout = pid.communicate()[0]
    if not pid.returncode == 0:
        raise ValueError("Error while executing %s: %s" % (" ".join(cmd), stdout))
    return stdout.strip()

print call_venv(["python", "setup.py", "install"])

for root, dirs, files in os.walk('examples'):
    for f in files:
        if os.path.basename(f) == "toysetup.info":
            print "========= testing package %s =============" % root
            print call_venv(["toymaker", "configure"], cwd=root)
            print call_venv(["toymaker", "build"], cwd=root)
            print call_venv(["toymaker", "install"], cwd=root)

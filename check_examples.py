import os
import subprocess
import shutil

from bento.core import PackageDescription
from bootstrap import main

main()

tests = []
for root, d, files in os.walk("examples"):
    if os.path.exists(os.path.join(root, "bento.info")):
        if not os.path.exists(os.path.join(root, os.pardir, "bento.info")):
            tests.append(root)

def use_waf(d):
    old_cwd = os.getcwd()
    try:
        os.chdir(d)
        package = PackageDescription.from_file("bento.info")
        return "Waf" in package.use_backends
    finally:
        os.chdir(old_cwd)

def test_package(d):
    def _run():
        for bcmd in [["configure"], ["build"], ["install", "--list-files"]]:
            cmd = [bentomaker] + bcmd
            p = subprocess.Popen(cmd, cwd=test, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            p.wait()
            if p.returncode:
                print(p.stdout.read().decode())
                return False
        return True
    if use_waf(d) and not "WAFDIR" in os.environ:
        print("waf test and WAFDIR not set, skipped")
        return True
    if os.path.exists(os.path.join(d, "build")):
        shutil.rmtree(os.path.join(d, "build"))
    if _run():
        # We run twice to check that re-running commands with various bento caching
        # does not blow up
        return _run()
    else:
        return False

nerrors = 0
bentomaker = os.path.join(os.getcwd(), "bentomaker")
for test in tests:
    print("=============== testing %s ==============" % test)
    if not test_package(test):
        print("Failed")
        nerrors += 1
    else:
        print("Succeeded")
print("%d / %d example failed" % (nerrors, len(tests)))

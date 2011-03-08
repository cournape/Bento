import os
import subprocess
import shutil

tests = []
for root, d, files in os.walk("examples"):
    if os.path.exists(os.path.join(root, "bento.info")):
        if not os.path.exists(os.path.join(root, os.pardir, "bento.info")):
            tests.append(root)

def test_package(d):
    def _run():
        for bcmd in [["configure"], ["build"], ["install", "--list-files"]]:
            cmd = [bentomaker] + bcmd
            p = subprocess.Popen(cmd, cwd=test, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            p.wait()
            if p.returncode:
                print p.stdout.read()
                return False
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
    print "=============== testing %s ==============" % test
    if not test_package(test):
        print "Failed"
        nerrors += 1
    else:
        print "Succeeded"
print "%d / %d example failed" % (nerrors, len(tests))

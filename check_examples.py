import os
import subprocess

tests = []
for root, d, files in os.walk("examples"):
    if os.path.exists(os.path.join(root, "bento.info")):
        if not os.path.exists(os.path.join(root, os.pardir, "bento.info")):
            tests.append(root)

def test_package(d):
    for bcmd in [["configure"], ["build"], ["install", "--list-files"]]:
        cmd = [bentomaker] + bcmd
        p = subprocess.Popen(cmd, cwd=test, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.wait()
        if p.returncode:
            print p.stdout.read()
            return False
    return True

bentomaker = os.path.join(os.getcwd(), "bentomaker")
for test in tests:
    print "=============== testing %s ==============" % test
    if not test_package(test):
        print "Failed"
    else:
        print "Succeeded"

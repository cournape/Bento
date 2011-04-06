#! /bin/sh
tests="examples/chaining/build.py
examples/conf_example.py
examples/example4.py
examples/example5.py
examples/c/example.py
examples/c/try_example.py
examples/file_hook.py
examples/fortran/conf_fortran.py
examples/fortran/fortran.py
examples/node_example.py
examples/override_ext.py
examples/pyext_example.py
examples/test_env.py
examples/subst_tool/example.py"

nerrors=0
ntests=0
nerrors3=0
ntests3=0
old_PYTHONPATH=$PYTHONPATH
PYTHONPATH=$PWD:$PYTHONPATH

PYTHON2=python2.6

for i in $tests; do
	echo "======== TESTING $i ============="
	f=`basename $i`;
	d=`dirname $i`;
	rm -rf $d/build;
	(cd $d && $PYTHON2 $f);
	if test $? -ne 0; then
		nerrors=`expr $nerrors + 1`;
	fi
	ntests=`expr $ntests + 1`;
done

python3.1 setup.py build
export PYTHONPATH=$PWD/build/py3k
for i in $tests; do
	echo "======== TESTING $i ============="
	f=`basename $i`;
	d=`dirname $i`;
	rm -rf $d/build;
	(cd $d &&  python3.1 $f);
	if test $? -ne 0; then
		nerrors3=`expr $nerrors3 + 1`;
	fi
	ntests3=`expr $ntests3 + 1`;
done

echo "PY2 errors: $nerrors/$ntests | PY3 errors: $nerrors3/$ntests3"

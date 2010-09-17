#! /bin/sh
tests="examples/chaining/build.py
examples/conf_example.py
examples/example4.py
examples/example5.py
examples/c/example.py
examples/file_hook.py
examples/fortran/conf_fortran.py
examples/fortran/fortran.py
examples/node_example.py
examples/override_ext.py
examples/pyext_example.py
examples/test_env.py"

nerrors=0
old_PYTHONPATH=$PYTHONPATH
PYTHONPATH=$PWD:$PYTHONPATH

for i in $tests; do
	echo "======== TESTING $i ============="
	f=`basename $i`;
	d=`dirname $i`;
	rm -rf $d/build;
	(cd $d && python $f);
	if test $? -ne 0; then
		nerrors=`expr $nerrors + 1`;
	fi
done

python3.1 setup.py build
export PYTHONPATH=$PWD/build/py3k
nerrors3=0
for i in $tests; do
	echo "======== TESTING $i ============="
	f=`basename $i`;
	d=`dirname $i`;
	rm -rf $d/build;
	(cd $d &&  python3.1 $f);
	if test $? -ne 0; then
		nerrors3=`expr $nerrors3 + 1`;
	fi
done

echo "PY2 errors: $nerrors | PY3 errors: $nerrors3"

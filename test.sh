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
for i in $tests; do
	echo "======== TESTING $i ============="
	f=`basename $i`;
	d=`dirname $i`;
	rm -rf $d/build;
	(cd $d && python $f);
done
python3.1 setup.py build
export PYTHONPATH=$PWD/build/py3k
for i in $tests; do
	echo "======== TESTING $i ============="
	f=`basename $i`;
	d=`dirname $i`;
	rm -rf $d/build;
	(cd $d &&  python3.1 $f);
done

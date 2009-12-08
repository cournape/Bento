from distutils.core import \
        setup
from distutils.command.install import \
        install

class my_install(install):
    def finalize_options(self):
        install.finalize_options(self)

if __name__ == '__main__':
    dist = setup(
        name='example',
        version='1.0',
        url='http://www.example.com',
        author='John Doe',
        author_email='john@doe.com',
        packages=['foo'],
        package_data={'foo': ['data/*.dat']},
        data_files=[('etc', ['cfg/data.cfg'])],
        cmdclass={'install': my_install},
        )

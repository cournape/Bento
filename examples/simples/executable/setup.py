from setuptools import setup

setup(name="simple_executable",
      version="0.1",
      entry_points={
          "console_scripts": [
            "simple_executable=foo.commands:main",
            "simple_executable2=foo.commands:main",
          ]
      }
)

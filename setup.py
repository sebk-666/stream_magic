""" setup.py
"""
from __future__ import print_function
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import io
import codecs
import os
import sys
import stream_magic

here = os.path.abspath(os.path.dirname(__file__))

def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read('README.txt')

class PyTest(TestCommand):
    """ n/a
    """
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(
    name='stream_magic',
    version=stream_magic.__version__,
    url='http://github.com/sebk-666/stream_magic/',
    license='Apache Software License',
    author='Sebastian Kaps',
    tests_require=['pytest'],
    install_requires=[],
    cmdclass={'test': PyTest},
    author_email='seb.kaps@zoho.com',
    description='Support for controlling and querying network audio players\
                based on the StreamMagic platform by Cambridge Audio',
    long_description=long_description,
    packages=['stream_magic'],
    include_package_data=True,
    platforms='any',
    test_suite='tests.test_stream_magic',
    classifiers=[            # https://pypi.org/pypi?%3Aaction=list_classifiers
        'Programming Language :: Python',
        'Development Status :: 3 - Alpha',
        'Natural Language :: English',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Home Automation',
        ],
    extras_require={
        'testing': ['pytest'],
    }
)

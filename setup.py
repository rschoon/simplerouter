#!/usr/bin/env python

import os
import re
from setuptools import setup

def read(filename):
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        return f.read()

def read_version(filename):
    return re.search(r"__version__ = '(.*?)'", read(filename)).group(1)

setup(
    name = 'simplerouter',
    version = read_version('simplerouter.py'),
    description = 'A very simple WebOb based router',
    long_description = read("README.rst"),
    author = 'Robin Schoonover',
    author_email = 'robin@cornhooves.org',
    url = "http://bitbucket.org/rschoon/simplerouter",
    license = 'MIT',
    install_requires = ['WebOb>=1.2.3'],
    py_modules = ['simplerouter'],
    test_suite = 'nose.collector',
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
    ],
)

#!/usr/bin/env python

import os
import re
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'simplerouter.py')) as v:
    VERSION = re.search(r"__version__ = '(.*?)'", v.read()).group(1)

setup(
    name = 'simplerouter',
    version = VERSION,
    description = 'A very simple WebOb based router',
    author = 'Robin Schoonover',
    author_email = 'robin@cornhooves.org',
    url = "http://bitbucket.org/rschoon/simplerouter",
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

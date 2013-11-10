
import sys, os
import re

with open(os.path.join(os.path.dirname(__file__), '..', 'simplerouter.py')) as v:
    version = re.search(r"__version__ = '(.*?)'", v.read()).group(1)

extensions = []

source_suffix = '.rst'
master_doc = 'index'

project = 'simplerouter'
copyright = '2013, Robin Schoonover'
release = version

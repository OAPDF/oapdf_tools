import codecs
from setuptools import setup
from setuptools import find_packages

with codecs.open('README.md', 'r', 'utf-8') as f:
    readme = f.read()

with codecs.open('Changelog.rst', 'r', 'utf-8') as f:
    changes = f.read()

long_description = '\n\n' + readme + '\n\n' + changes

setup(
	name             = 'oapdftools',
	version          = '0.1.0.0',
	description      = 'Tools for OAPDF',
	long_description = long_description,
  author           = 'OAPDF',
  author_email     = 'oapdf@hotmail.com',
  url              = 'https://github.com/OAPDF/oapdftools',
  license          = 'MIT',
  packages         = find_packages(exclude=['test-*']),
  scripts		   = ['tools/oapdftool.py'],
  install_requires = ['requests>=2.7.0', 'pdfminer'],
  classifiers      = (
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Science/Research',
    'Intended Audience :: Developers',
    'Topic :: Scientific/Engineering :: Bio-Informatics',
    'Natural Language :: English',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3'
	)
)

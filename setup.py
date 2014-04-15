#!/usr/bin/env python
"""
  Copyright 2012-2013 The MASTIFF Project, All Rights Reserved.

  This software, having been partly or wholly developed and/or
  sponsored by KoreLogic, Inc., is hereby released under the terms
  and conditions set forth in the project's "README.LICENSE" file.
  For a list of all contributors and sponsors, please refer to the
  project's "README.CREDITS" file.
"""

__doc__ = """
This file is the setup/install script for MASTIFF.
"""

import sys
from setuptools import setup, find_packages
from mastiff import get_release_string

if sys.version_info < (2, 6, 6):
    sys.stderr.write("Mastiff requires python version 2.6.6")
    sys.exit(1)
    
setup(
    author='Tyler Hudak',
    author_email='mastiff-project@korelogic.com',
    data_files=[('config', ['mastiff.conf'])],
    description="""MASTIFF is a static analysis automation framework.""",
    install_requires=['Yapsy == 1.10, !=1.10-python3'],
    license='Apache License V2.0',
    long_description="""MASTIFF is a static analysis framework that automates the
process of extracting key characteristics from a number of different file
formats. To ensure the framework remains flexible and extensible, a
community-driven set of plug-ins is used to perform file analysis and data
extraction. While originally designed to support malware, intrusion, and
forensic analysis, the framework is well-suited to support a broader range of
analytic needs. In a nutshell, MASTIFF allows analysts to focus on analysis
rather than figuring out how to parse files.""",
    maintainer='Tyler Hudak',
    maintainer_email='mastiff-project@korelogic.com',
    name='mastiff',        
    packages=find_packages(), 
    package_data={'': ['*.py', '*.yapsy-plugin'] },
    platforms=['Linux'],
    scripts=['mas.py'],
    url='http://www.korelogic.com',
    version=get_release_string())


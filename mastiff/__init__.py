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
MASTIFF - MAlicious Static Inspection File Framework

This program implements the code necessary to statically analyze files within
a plugin-based framework.

"""

"""
This file contains package-level variables and functions.
"""

__version__ = "$Id$"

version = 0x00700001

def get_release_number():
    """ Gets the current release version. """
    return version

def get_release_string():
    """Return the current release version."""
    major = (version >> 28) & 0x0f
    minor = (version >> 20) & 0xff
    patch = (version >> 12) & 0xff
    state = (version >> 10) & 0x03
    build = version & 0x03ff
    if state == 0:
        state_string = "ds"
    elif state == 1:
        state_string = "rc"
    elif state == 2:
        state_string = "sr"
    elif state == 3:
        state_string = "xs"
    if state == 2 and build == 0:
        return '%d.%d.%d' % (major, minor, patch)
    else:
        return '%d.%d.%d.%s%d' % (major, minor, patch, state_string, build)


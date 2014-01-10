#!/usr/bin/env python
"""
  Copyright 2012-2013 The MASTIFF Project, All Rights Reserved.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
"""

"""
  This file contains package-level variables and functions.
"""

__version__ = "$Id: __init__.py,v 1.20 2013/04/18 20:11:24 klm Exp $"

version = 0x00600800

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


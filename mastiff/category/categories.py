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
The base category classes for each of the file types analyzed by
mastiff.
"""

__version__ = "$Id$"

from yapsy.IPlugin import IPlugin

class MastiffPlugin(IPlugin):
    """The base plugin class every category class should inherit."""

    def __init__(self, name=None):
        """Initialize the Mastiff plugin class."""
        IPlugin.__init__(self)
        self.name = name
        self.prereq = None

    def activate(self):
        """Power rings activate! Form of Mastiff Plugin!"""
        IPlugin.activate(self)

    def deactivate(self):
        """Deactivate plugin."""
        IPlugin.deactivate(self)

    def set_name(self, name=None):
        """
           Yapsy does not provide an easy way to get or set our own
           name, so here's a function to do so.
        """
        self.name = name
        return self.name


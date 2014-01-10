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
Functions to parse and maintain the Mastiff config file.

The Conf class is used to parse and maintain the Mastiff config file.

_init__(self, config_file=None, override=None): Initializes the config file and
sets up any overridden options.

get_var(section, var): Return a variable from a specified section.

get_bvar(section, var): Return a boolean variable from a specified section.

set_var(section, var, value): Set a variable in a specified section with a
                              given value.

get_section(section): Return a dictionary of items within the section.

list_config(): Prints all configuration variables read in.

dump_config(): Dump a copy of the config into the Mastiff log dir.

override_option(): Override an option from the config file.

"""

__version__ = "$Id: conf.py,v 1.16 2013/03/04 15:38:52 thudak Exp $"

import os
import sys
import logging
import ConfigParser

class Conf:
    """Parse and maintain the Mastiff configuration."""

    def __init__(self, config_file=None, override=None):
        """Initialize the class parameters."""

        log = logging.getLogger('Mastiff.Conf')

        self.config_file = os.path.abspath(config_file)

        self.config = ConfigParser.ConfigParser()
        self.set_defaults()

        # read from the default file locations and the file given
        # file given will be read last and will over-write any
        # previously read-in config files
        files_read = self.config.read([ '/etc/mastiff/mastiff.conf',
                                        os.path.expanduser('~/.mastiff.conf'),
                                        config_file])

        if not files_read:
            log.error("Could not read any configuration files. Exiting.")
            sys.exit(1)
        else:
            if self.config.getboolean('Misc', 'verbose') == True:
                log.setLevel(logging.DEBUG)
                log.debug("Read config from %s", str(files_read))

        if override is not None:
            for opt in override:
                self.override_option(opt)

    def set_defaults(self):
        """
           Set default variables.
           If set later in a config file, these will be overwritten.
           Note: This is being done instead of a default config file to
           reduce the number of files needed.
        """
        self.config.add_section('Dir')
        self.set_var('Dir', 'log_dir', '/var/log/mastiff')
        self.set_var('Dir', 'plugin_dir', '/usr/local/mastiff/plugins')
        self.config.add_section('Misc')
        self.set_var('Misc', 'verbose', 'off')

    def get_var(self, section, var):
        """Return a specified variable."""
        try:
            return self.config.get(section, var)
        except ConfigParser.NoOptionError:
            log = logging.getLogger('Mastiff.Conf.GetVar')
            log.error('Could not find "%s": "%s"', section, var)
            return None

    def get_bvar(self, section, var):
        """Return a boolean variable."""
        try:
            return self.config.getboolean(section, var)
        except ConfigParser.NoOptionError:
            log = logging.getLogger('Mastiff.Conf.GetVar')
            log.error('Could not find "%s": "%s"', section, var)
            return None

    def get_section(self, section):
        """Return a dictionary of items within a section."""
        try:
            options = self.config.items(section)
        except ConfigParser.NoSectionError:
            log = logging.getLogger('Mastiff.Conf.GetSection')
            log.error('Could not get section "%s".', section)
            return None

        opt_dict = dict()

        for pairs in options:
            opt_dict[pairs[0]] = pairs[1]

        return opt_dict

    def set_var(self, section, var, value):
        """Set a given variable with a specified value."""
        try:
            return self.config.set(section, var, value)
        except ConfigParser.NoSectionError:
            log = logging.getLogger('Mastiff.Conf.SetVar')
            log.error('Could not find "%s": "%s"', section, var)
            return None

    def override_option(self, override):
        """
           Override an option from the config file. Note that if the option
           does not exist, it will be added.
        """
        log = logging.getLogger('Mastiff.Conf.override')
        options = override.split('=')
        section = options[0].split('.')

        if len(options) != 2 or len(section) != 2:
            log.error('Invalid override option: %s' % override)
            return False

        log.info('Overriding option: %s.%s=%s' % (section[0], section[1], options[1]))
        if self.set_var(section[0], section[1], options[1]) is None:
            return False

    def list_config(self):
        """Print all variables read in."""
        print "Configuration Options:"
        for section in self.config.sections():
            print "%s" % (section)
            for (name, value) in self.config.items(section):
                print "\t%s:\t%s" % (name, value)
        return

    def dump_config(self):
        """ Dump a copy of the config into the Mastiff log dir. """

        log = logging.getLogger('Mastiff.Conf.Dump')
        out_dir = self.get_var('Dir',  'log_dir')

        try:
            with open(out_dir + os.sep + 'mastiff-run.config',  'w') as dump_file:
                self.config.write(dump_file)
        except ConfigParser.Error,  err:
            log.error('Unable to dump config file: %s',  err)


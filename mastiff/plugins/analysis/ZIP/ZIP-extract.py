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
Zip archive extract plug-in.

Plugin Type: ZIP
Purpose:
  Extract all of the files within the archive into a directory.

  If the filename contains an absolute path or '..'s, they are removed before
  extraction occurs.

Configuration Options:

  enabled = [on|off]: Whether you want to submit files to VT or not.

Output:
   Extracts all of the files in the archive to log_dir/zip_contents.

"""

__version__ = "$Id$"

import logging
import os
import zipfile
import struct

import mastiff.plugins.category.zip as zip
import mastiff.queue as queue

class ZIP_Extract(zip.ZipCat):
    """Zip archive extraction plug-in."""

    def __init__(self):
        """Initialize the plugin."""
        zip.ZipCat.__init__(self)

    def activate(self):
        """Activate the plugin."""
        zip.ZipCat.activate(self)

    def deactivate(self):
        """Deactivate the plugin."""
        zip.ZipCat.deactivate(self)

    def analyze(self, config, filename):
        """Analyze the file."""

        # sanity check to make sure we can run
        if self.is_activated == False:
            return False

        log = logging.getLogger('Mastiff.Plugins.' + self.name)
        log.info('Starting execution.')

        feedback = config.get_bvar(self.name,  'feedback')

        if feedback is True:
            job_queue = queue.MastiffQueue(config.config_file)
        else:
            job_queue = None

        # make sure we are enabled
        if config.get_bvar(self.name, 'enabled') is False:
            log.info('Disabled. Exiting.')
            return True

        try:
            my_zip = zipfile.ZipFile(filename, 'r', allowZip64=True)
        except (zipfile.BadZipfile, IOError, struct.error), err:
            log.error('Unable to open zip file: {}'.format(err))
            return False

        log_dir = config.get_var('Dir', 'log_dir')
        log_dir += os.sep + 'zip_contents'
        try:
            os.mkdir(log_dir)
        except OSError, err:
            # dir already exists, skip
            pass

        # grab password if one exists
        pwd = config.get_var(self.name, 'password')
        if pwd is not None and len(pwd) > 0:
            log.info('Password \"{}\" will be used for this zip.'.format(pwd))

        # cycle through files and extract them
        for file_member in my_zip.namelist():

            # if its an absolute directory, remove os.sep
            if file_member[0:1] == os.sep:
                log.info('Zip member \"{}\" contains absolute path. Stripping.'.format(file_member))
                zipfile_name = os.path.normpath(file_member[1:])
            
            try:
                zipfile_name = unicode(os.path.normpath(file_member))
            except UnicodeDecodeError:
                 zipfile_name = unicode(os.path.normpath(file_member), errors='replace')

            # warn about the ..'s, normpath above removes them
            if os.pardir in file_member:
                log.warning('File contains ..s: {}'.format(file_member))

            # we can't just blindly extract in case there are absolute paths or '..'s
            # so we read in the file, create any directories, and write it out
            try:
                log.debug('Creating directory {}.'.format(os.path.dirname(zipfile_name.encode('utf-8'))))
                os.makedirs(log_dir + os.sep + os.path.dirname(zipfile_name))
            except OSError, err:
                log.debug('Directory {} already exists.'.format(os.path.dirname(zipfile_name.encode('utf-8'))))

            if len(os.path.basename(file_member)) == 0:
                log.debug('{} is just a directory. Not creating file.'.format(file_member.encode('utf-8')))
                continue

            log.info('Extracting {}.'.format(zipfile_name.encode('utf-8')))

            try:
                in_file = my_zip.open(file_member, 'r', pwd=pwd)
                data = in_file.read()
                in_file.close()
            except RuntimeError, err:
                log.error('Problem extracting: {}'.format(err.message.encode('utf-8')))
                continue
            except (IOError, zipfile.BadZipfile) as err:
                log.error('Problem extracting {}.'.format(file_member))
                log.error('Possible obfuscation or corruption: {}'.format(err.message))
                continue

            try:
                outfile = open(log_dir + os.sep + zipfile_name, 'w')
                outfile.write(data)
                outfile.close()

            except IOError, err:
                log.error('Could not write file: {}'.format(err))
                return False

            # now feed back to mastiff if asked to
            if job_queue is not None and feedback is True:
                log.info('Adding {} to queue.'.format(zipfile_name.encode('utf-8')))
                job_queue.append(log_dir + os.sep + zipfile_name)

        my_zip.close()

        return True


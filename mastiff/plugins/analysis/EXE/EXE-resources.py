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
PE Resources Plug-in

Plugin Type: EXE
Purpose:
  This plug-in obtains information on any resources contained within
  the Windows EXE and extracts them.

  More information on how resources are stored can be found in the
  Microsoft PE and COFF Specification document.
  http://msdn.microsoft.com/library/windows/hardware/gg463125

  Thanks to Ero Carrera for creating the pefile library, whose code helped
  understand how to process resources.

Output:
   resources.txt - File containing a list of all resources in the EXE and any
                  associated information.
   log_dir/resource - Directory containing any extracted resource.

Pre-requisites:
   - pefile library (http://code.google.com/p/pefile/)

"""

__version__ = "$Id$"

import logging
import os
import time

try:
    import pefile
except ImportError, err:
    print ("Unable to import pefile: %s" % err)

import mastiff.plugins.category.exe as exe

class EXE_Resources(exe.EXECat):
    """EXE Resources plugin code."""

    def __init__(self):
        """Initialize the plugin."""
        exe.EXECat.__init__(self)
        self.resources = list()
        self.pe = None

    def analyze_dir(self, directory, prefix='', _type='', timedate=0):
        """ Analyze a resource directory and obtain all of its items."""
        log = logging.getLogger('Mastiff.Plugins.' + self.name + '.analyze')

        # save the timedate stamp
        timedate = directory.struct.TimeDateStamp

        for top_item in directory.entries:

            if hasattr(top_item, 'data'):
                # at the language level that contains all of our information
                resource = dict()
                resource['Id'] = prefix
                resource['Type'] = _type
                # store the offset as the offset within the file, not the RVA!
                try:
                    resource['Offset'] = self.pe.get_offset_from_rva(top_item.data.struct.OffsetToData)
                    resource['Size'] = top_item.data.struct.Size
                    resource['Lang'] = [ pefile.LANG.get(top_item.data.lang, '*unknown*'), \
                                                            pefile.get_sublang_name_for_lang( top_item.data.lang, top_item.data.sublang ) ]
                    resource['TimeDate'] = timedate
                except pefile.PEFormatError, err:
                    log.error('Error grabbing resource \"%s\" info: %s' %  (prefix, err))
                    return False

                self.resources.append(resource)
                log.debug('Adding resource item %s' % resource['Id'])
            elif hasattr(top_item, 'directory'):
                if top_item.name is not None:
                    # in a name level
                    if len(prefix) == 0:
                        newprefix = prefix + str(top_item.name)
                    else:
                        newprefix = ', '.join([prefix, str(top_item.name)])
                else:
                    # if name is blank, we are in a Type level
                    if len(prefix) == 0:
                        newprefix = 'ID ' + str(top_item.id)
                        _type = pefile.RESOURCE_TYPE.get(top_item.id)
                    else:
                        newprefix = ', '.join([prefix,  'ID ' + str(top_item.id)])

                # we aren't at the end, recurse
                self.analyze_dir(top_item.directory, prefix=newprefix, _type=_type)

    def extract_resources(self, log_dir, filename):
        """
           Extract any resources from the file and put them in
           the resources dir.
        """

        log = logging.getLogger('Mastiff.Plugins.' + self.name + '.extract')

        if len(self.resources) == 0:
            # no resources
            return False

        # create the dir if it doesn't exist
        log_dir = log_dir + os.sep + 'resources'
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except IOError,  err:
                log.error('Unable to create dir %s: %s' % (log_dir, err))
                return False

        try:
            my_file = open(filename, 'rb')
        except IOError, err:
            log.error('Unable to open file.')
            return False

        file_size = os.path.getsize(filename)

        # cycle through resources and extract them
        for res_item in self.resources:

            # check to make sure we won't go past the EOF
            if (res_item['Offset'] + res_item['Size']) > file_size:
                log.error('File is smaller than resource location. Could be a packed file.')
                continue

            my_file.seek(res_item['Offset'])
            data = my_file.read(res_item['Size'])
            out_name = res_item['Id'].replace('ID ', '_').replace(', ', '_').lstrip('_')

            if res_item['Type'] is not None and len(res_item['Type']) > 0:
                out_name += '_' + res_item['Type']

            with open(log_dir + os.sep + out_name, 'wb') as out_file:
                log.debug('Writing %s to %s.' % (res_item['Id'], out_name))
                out_file.write(data)
                out_file.close()

        my_file.close()
        return True

    def analyze(self, config, filename):
        """Analyze the file."""

        # sanity check to make sure we can run
        if self.is_activated == False:
            return False
        log = logging.getLogger('Mastiff.Plugins.' + self.name)
        log.info('Starting execution.')

        try:
            self.pe = pefile.PE(filename)
        except pefile.PEFormatError, err:
            log.error('Unable to parse PE file: %s' % err)
            return False

        if not hasattr(self.pe, 'DIRECTORY_ENTRY_RESOURCE'):
            log.info('No resources for this file.')
            return False

        # parse the directory structure
        self.analyze_dir(self.pe.DIRECTORY_ENTRY_RESOURCE)

        if len(self.resources) == 0:
            log.info('No resources could be found.')
        else:
            # output data to file and extract resources
            self.output_file(config.get_var('Dir','log_dir'))
            self.extract_resources(config.get_var('Dir','log_dir'), filename)

        return True

    def output_file(self, outdir):
        """Print output from analysis to a file."""

        log = logging.getLogger('Mastiff.Plugins.' + self.name + '.output')

        try:
            outfile = open(outdir + os.sep + 'resources.txt', 'w')
            outfile.write('Resource Information\n\n')
        except IOError, err:
            log.error('Could not open resources.txt: %s' % err)
            return False

        outstr = '{0:20} {1:15} {2:15} {3:8} {4:<30} {5:<25}\n'.format( \
                                                                   'Name/ID',
                                                                   'Type',
                                                                   'File Offset',
                                                                   'Size',
                                                                   'Language',
                                                                   'Time Date Stamp')
        outfile.write(outstr)
        outfile.write('-' * len(outstr) + '\n')

        for item in sorted(self.resources, key=lambda mydict: mydict['Offset']):

            lang = ', '.join(item['Lang']).replace('SUBLANG_', '').replace('LANG_', '')
            my_time = time.asctime(time.gmtime(item['TimeDate']))

            outstr = '{0:20} {1:15} {2:<15} {3:<8} {4:30} {5:<25}\n'.format(item['Id'],
                                                             item['Type'],
                                                             hex(item['Offset']),
                                                             hex(item['Size']),
                                                             lang,
                                                             my_time)
            outfile.write(outstr)

        return True


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
PDF-pdfparser

Plugin Type: PDF
Purpose:
  This plug-in uses Didier Stevens pdf-parser.py code to perform two tasks:

  - Writes an uncompressed copy of the PDF to a file named uncompressed-pdf.txt
  - Searches the PDF for keywords in objects, specified by the
    self.interesting_objects list, and writes those objects, and any they
    reference, to a file in pdf-objects/.

  All rights for pdf-parser.py belong to Didier Stevens.

Requirements:
  - Didier Stevens pdf-parser.py must be installed.
    (http://blog.didierstevens.com/programs/pdf-tools/)

Configuration Options:

[pdf-parser]
pdf_cmd = Path to pdf-parser.py

"""

__version__ = "$Id$"

import os
import subprocess
import logging
import re

import mastiff.queue as queue
import mastiff.category.pdf as pdf

class PDFparser(pdf.PDFCat):
    """Plug-in to run Didier Stevens pdf-parser.py script."""

    def __init__(self):
        """Initialize the plugin."""
        pdf.PDFCat.__init__(self)

        # list of objects we want to search for
        self.interesting_objects = [ 'JavaScript', 'JS', 'OpenAction', 'AA' ]

    def analyze(self, config, filename):
        """
        Obtain the command and options from the config file and call the
        external program.
        """
        # make sure we are activated
        if self.is_activated == False:
            return False
        log = logging.getLogger('Mastiff.Plugins.' + self.name)
        log.info('Starting execution.')

        # get my config options
        plug_opts = config.get_section(self.name)
        if plug_opts is None:
            log.error('Could not get %s options.', self.name)
            return False

        # verify external program exists and we can call it
        if not plug_opts['pdf_cmd'] or \
           not os.path.isfile(plug_opts['pdf_cmd']) or \
           not os.access(plug_opts['pdf_cmd'], os.X_OK):
            log.error('%s is not accessible. Skipping.', plug_opts['pdf_cmd'])
            return False

        self.uncompress(config, plug_opts, filename)
        self.get_objects(config, plug_opts, filename)

        log.debug ('Successfully ran %s.', self.name)
        return True

    def output_object(self, plug_opts, pdf_file, obj_num, reasons, log_dir):
        """
           Run pdf-parser to extract a given obj_num and place
           it into the log_dir directory, in the form obj-#.txt.
        """
        log = logging.getLogger('Mastiff.Plugins.' + self.name + '.outobj')

        # create the dir if it doesn't exist
        log_dir = log_dir + os.sep + 'pdf-objects'
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except IOError,  err:
                log.error('Unable to create dir %s: %s' % (log_dir, err))
                return False

        # if we get the obj_num in the form "12 0", remove the gen #
        if ' ' in obj_num:
            # contains whitespace
            obj_num = obj_num.split(' ')[0]

        filename = log_dir + os.sep + 'obj-' + obj_num + '.txt'

        # have pdf-parser extract the object for us
        options = list(['-o ' + obj_num, '-f', '-w'])
        run = subprocess.Popen([plug_opts['pdf_cmd']] + \
                               options + \
                               [ pdf_file ],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               close_fds=True)
        (output, error) = run.communicate()
        if error is not None and len(error) > 0:
            log.error('Unable to extract object %s.' % obj_num)
            return False

        # output the file - we don't use the pdf-parser.py -d option as
        # there are times it errors out when attempting to dump an object
        with open(filename, 'w') as out_file:
            out_file.write('Object %s\n' % obj_num)
            out_file.write('Flagged due to:\n')
            for why in reasons:
                out_file.write('\t%s\n' % why)
            out_file.write('\n')
            out_file.write(output)

        return True

    def get_objects(self, config, plug_opts, filename):
        """ Search through the PDF for objects associated with malicious
            activity and extract those into their own file.
        """
        log = logging.getLogger('Mastiff.Plugins.' + self.name + '.get_objects')
        log.info('Extracting interesting objects.')

        #objects = list()
        objects = dict()

        for keyword in self.interesting_objects:
            # let pdf-parser.py grab the object containing our keywords
            run = subprocess.Popen([plug_opts['pdf_cmd']] + \
                                             ['--search=' + keyword ] +
                                             [ filename ],
                                             stdin=subprocess.PIPE,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE, 
                                             close_fds=True)
            (output, error) = run.communicate()
            # skip anything that gives us an error
            if error is not None and len(error) > 0:
                continue

            # go through pdf-parser output and grab any objects and
            # their referenced objects to dump
            for line in output.split('\n'):
                obj_match = re.match('obj\s+([0-9]+\s+[0-9]+)', line)
                ref_match = re.search('Referencing: ([0-9]+\s+[0-9\s,R]+)', line)

                if obj_match is not None:
                    # obj # #
                    cur_obj = obj_match.group(1)
                    if cur_obj not in objects.keys():
                        objects[cur_obj] = list()
                    objects[cur_obj].extend(['Keyword: %s' % keyword ])
                    log.debug('Adding object %s for keyword %s' % (cur_obj, keyword))
                elif ref_match is not None:
                    # Referenced by: object list
                    for ref_obj in \
                    [ x.lstrip()[:-2] for x in ref_match.group(1).split(',')]:
                        if ref_obj not in objects.keys():
                            # item not created yet
                            objects[ref_obj] = list()
                        if 'Referenced by %s' % cur_obj not in objects[ref_obj]:
                            # make sure we didn't add already
                            objects[ref_obj].extend(['Referenced by %s' % cur_obj ])
                            log.debug('Adding object %s from reference "%s"' % (ref_obj, cur_obj))

        # output collected objects to file
        for my_obj in objects.keys():
            self.output_object(plug_opts,
                               filename,
                               my_obj,
                               objects[my_obj],
                               config.get_var('Dir', 'log_dir'))

    def uncompress(self, config, plug_opts,  filename):
        """ Uncompress the PDF using pdf-parser.py """
        log = logging.getLogger('Mastiff.Plugins.' + self.name + '.uncompress')
        log.info('Uncompressing PDF.')
        
        feedback = config.get_bvar(self.name,  'feedback')
        if feedback is True:
            job_queue = queue.MastiffQueue(config.config_file)
        else:
            job_queue = None        

        # run pdf-parser with -w (raw) and -f (decompress) opts
        run = subprocess.Popen([plug_opts['pdf_cmd']] + \
                               ['-w', '-f' ] +
                               [ filename ],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               close_fds=True)

        (output, error) = run.communicate()
        if error is not None and len(error) > 0:
            log.error('Unable to uncompress PDF: %s.' % filename)
            return False

        self.output_file(config.get_var('Dir', 'log_dir'), output)
        
        if job_queue is not None and feedback is True and not filename.endswith('uncompressed-pdf.txt'):
            log.info('%s' % filename)
            log.info('Adding uncompressed PDF to queue.')
            job_queue.append(config.get_var('Dir', 'log_dir') + os.sep + "uncompressed-pdf.txt")

    def output_file(self, outdir, data):
        """Place the data into a file."""
        log = logging.getLogger('Mastiff.Plugins.' + self.name)

        try:
            out_file = open(outdir + os.sep + "uncompressed-pdf.txt",'w')
        except IOError, err:
            log.error('Write error: %s', err)
            return False

        out_file.write(data)
        out_file.close()
        return True


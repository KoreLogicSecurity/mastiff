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
MASTIFF Online Submission Plug-in

Plugin Type: Generic
Purpose:
  This plug-in provides an interface to upload a file to MASTIFF Online.

Output:
   None
"""

__version__ = "$Id$"

import logging
import mastiff.plugins as plugins
import simplejson as json
import os
import sys

# Change the following line to import the category class you for the files
# you wish to perform analysis on
import mastiff.plugins.category.generic as gen

# Change the class name and the base class
class GenMastiffOnline(gen.GenericCat):
    """MASTIFF Online plugin code."""

    def __init__(self):
        """Initialize the plugin."""
        gen.GenericCat.__init__(self)
        self.page_data.meta['filename'] = 'MASTIFF-online'

    def activate(self):
        """Activate the plugin."""
        gen.GenericCat.activate(self)

    def deactivate(self):
        """Deactivate the plugin."""
        gen.GenericCat.deactivate(self)

    def analyze(self, config, filename):
        """Analyze the file."""

        # sanity check to make sure we can run
        if self.is_activated == False:
            return False
        log = logging.getLogger('Mastiff.Plugins.' + self.name)
        log.info('Starting execution.')
        
        # get terms of service acceptance
        tos = config.get_bvar(self.name,  'accept_terms_of_service')
        if tos is None or tos is False:
            log.info('Terms of service not accepted. Accept to enable MASTIFF Online submission.')
            return self.page_data
        
        myjson = None
        
        submit = config.get_bvar(self.name,  'submit')
        if submit is False:
            log.info('Not configured to send to MASTIFF Online.')
            return self.page_data
            
        # send data to MASTIFF Online server
        host = 'mastiff-online.korelogic.com'
        method = 'https'
        selector="/cgi/dispatcher.cgi/UploadMOSample"
        fields = [('accept_terms_of_service',  'true')]
        file_to_send = open(filename, "rb").read()        
        files = [("upload", os.path.basename(filename), file_to_send)]
        log.debug('Sending sample to MASTIFF Online.')
        response = plugins.post_multipart(host, method, selector, fields, files)

        # what gets returned isn't technically JSON, so we have to manipulate it a little bit
        try:
            myjson = json.loads(response[60:-14].replace('\'','\"'))
        except json.scanner.JSONDecodeError, err:
            log.error('Error processing response: {}'.format(err))
        except:
            e = sys.exc_info()[0]
            log.error('Error processing incoming response: {}.'.format(e))       
        
        if myjson is not None:
            self.gen_output(myjson)
            
        return self.page_data

    def gen_output(self, myjson):
        """Place the results into a Mastiff Output Page."""
        log = logging.getLogger('Mastiff.Plugins.' + self.name)

        mytable = self.page_data.addTable('MASTIFF Online')
        mytable.addheader([('name', str), ('data', str)], printHeader=False)
        mytable.addrow(['Sample Uploaded On', myjson['sample_uploaded_on']])

        if myjson['sample_state'] == 'todo':
            mytable.addrow(['Status', 'In queue'])            
        elif myjson['sample_state'] == 'done':
            mytable.addrow(['Status', 'Completed'])
        else:
            mytable.addrow(['Status', myjson['sample_state']])
            
        mytable.addrow(['URL', 'https://mastiff-online.korelogic.com/index.html?sample_hash_md5=' + myjson['sample_hash_md5']])        
        

        return True


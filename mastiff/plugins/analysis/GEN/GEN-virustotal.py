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
VirusTotal Submission plugin

Plugin Type: Generic
Purpose:
  This plug-in determines if the file being analyzed has been analyzed on
  www.virustotal.com previously.

  Information on the VT API can be found at:
  https://www.virustotal.com/documentation/public-api/

Requirements:
  - A VirusTotal API key is required to be entered into the configuration file.
    This can be obtained from virustotal.com.

  - The simplejson module must be present. (https://github.com/simplejson/simplejson)

Configuration Options:

  api_key: Your API key from virustotal.com. Leave this blank to disable the
  plug-in.

  submit [on|off]: Whether you want to submit files to VT or not.

Output:
   The results from VirusTotal retrieval or submission will be placed into
   virustotal.txt.

Note:
   Unless special arrangements are made, VT will not let you send more than 4
   queries in a 1 minute timeframe. You may receive errors if you do.

"""

__version__ = "$Id$"

import logging
import simplejson
import urllib
import urllib2
import os
import socket

import mastiff.plugins as plugins
import mastiff.plugins.category.generic as gen

class GenVT(gen.GenericCat):
    """VirusTotal plugin code."""

    def __init__(self):
        """Initialize the plugin."""
        self.api_key = None
        gen.GenericCat.__init__(self)

    def retrieve(self,  md5):
        """
           Retrieve results for this hash from VT.
           This code based on the code from the VT API documentation.
        """

        log = logging.getLogger('Mastiff.Plugins.' + self.name + '.retrieve')

        url = "https://www.virustotal.com/vtapi/v2/file/report"
        parameters =  dict()
        parameters['apikey'] = self.api_key
        # set resource to the MD5 hash of the file
        parameters['resource'] = md5

        # set up request
        log.debug('Submitting request to VT.')

        data = urllib.urlencode(parameters)
        try:
            req = urllib2.Request(url, data)
            response = urllib2.urlopen(req)
        except urllib2.HTTPError, err:
            log.error('Unable to contact URL: %s',  err)
            return None
        except urllib2.URLError, err:
            log.error('Unable to open connection: %s', err)
            return None
        except:
            log.error('Unknown Error when opening connection.')
            return None

        json = response.read()
        try:
            response_dict = simplejson.loads(json)
        except simplejson.decoder.JSONDecodeError:
            log.error('Error in VT JSON response. Are you submitting too fast?')
            return None
        else:
            log.debug('Response received.')
            return response_dict

    def submit(self, config, filename):
        """
            Submit a file to VT for analysis.
            This code based on the code from the VT API documentation.

            Note: This function will likely fail if a proxy is used.
        """
        log = logging.getLogger('Mastiff.Plugins.' + self.name + '.submit')

        try:
            outdir = config.get_var('Dir', 'log_dir')
            vt_file  = open(outdir + os.sep + 'virustotal.txt', 'w')
        except IOError,  err:
            log.error('Unable to open %s for writing: %s',
                      outdir + 'virustotal.txt',  err)
            return False

        # make sure we are allowed to submit
        if config.get_bvar(self.name, 'submit') == False:
            log.info('Submission disabled. Not sending file.')
            vt_file.write('File not submitted because submission disabled.\n')
            vt_file.close()
            return False

        log.info('Sending file to VirusTotal')

        # send file to VT
        host = "www.virustotal.com"
        selector = "https://www.virustotal.com/vtapi/v2/file/scan"
        fields = [("apikey", config.get_var(self.name, 'api_key'))]
        file_to_send = open(filename, "rb").read()
        files = [("file", os.path.basename(filename), file_to_send)]
        try:
            json = simplejson.loads(plugins.post_multipart(host, selector,
                                                           fields, files))
        except socket.error, err:
            log.error('Unable to send file: %s' % err)
            return False

        # check for success
        if json['response_code'] != 1:
            # error
            log.error('Could not submit to VT:\n%s', json['verbose_msg'])
            return False

        # write to file
        vt_file.write(json['verbose_msg'] + '\n')
        vt_file.write('Link:\n' + json['permalink'] + '\n')
        vt_file.close()

        return True

    def analyze(self, config, filename):
        """Analyze the file."""

        # sanity check to make sure we can run
        if self.is_activated == False:
            return False
        log = logging.getLogger('Mastiff.Plugins.' + self.name)
        log.info('Starting execution.')

        self.api_key = config.get_var(self.name,  'api_key')
        if self.api_key is None or len(self.api_key) == 0:
            log.error('No VirusTotal API Key - exiting.')
            return False

        md5 = config.get_var('Misc',  'hashes')[0]

        response = self.retrieve(md5)
        if response is None:
            # error occurred
            log.error('Did not get a response from VT. Exiting.')
            return False

        # response of 1 means it has been scanned on VT before
        # response of 0 means that is has not
        if response['response_code'] != 1:
            # The file has not been submitted
            self.submit(config, filename)
        else:
            # write response to file
            self.output_file(config.get_var('Dir',  'log_dir'), response)

        return True

    def output_file(self, outdir, response):
        """Format the output from VT into a file. """
        log = logging.getLogger('Mastiff.Plugins.' + self.name + 'output_file')

        try:
            vt_file  = open(outdir + os.sep + 'virustotal.txt',  'w')
        except IOError,  err:
            log.error('Unable to open %s for writing: %s',
                      outdir + 'virustotal.txt',  err)
            return False

        vt_file.write('VirusTotal Results for %s\n' % response['md5'])
        vt_file.write('Last scan date: %s\n' % response['scan_date'])
        vt_file.write('Total positive results: %d/%d\n' % \
                      (response['positives'],  response['total']))
        vt_file.write('Link to virustotal.com:\n%s\n\n' % response['permalink'])

        if response['positives'] > 0:
            vt_file.write('{0:25} {1:15} {2:40}\n'.format('AV', 'Version', 'Results'))

            for av_key in sorted(response['scans'].keys(), key=lambda s: s.lower()):

                if response['scans'][av_key]['detected'] == True:
                    out_str = '{0:25} {1:15} {2:40}\n'
                    out_str = out_str.format(av_key, \
                                             response['scans'][av_key]['version'], \
                                             response['scans'][av_key]['result'])
                    vt_file.write(out_str)

        vt_file.close()
        return True


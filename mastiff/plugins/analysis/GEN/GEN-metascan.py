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
Metascan Online Submission plugin

Plugin Type: Generic
Purpose:
  This plug-in determines if the file being analyzed has been analyzed on
  www.metascan-online.com previously.

  Information on the Metascan Online API can be found at:
  https://www.metascan-online.com/en/public-api

Requirements:
  - A Metascan Online API key is required to be entered into the configuration file.
    This can be obtained from www.metascan-online.com.

  - The simplejson module must be present. (https://github.com/simplejson/simplejson)

Configuration Options:

  api_key: Your API key from metascan-online.com. Leave this blank to disable the
  plug-in.

  submit [on|off]: Whether you want to submit files to the site or not.

Output:
   The results from Metascan Online retrieval or submission will be placed into
   metascan-online.txt.

"""

__version__ = "$Id$"

import logging
import simplejson
import urllib2
import os
import socket

import mastiff.plugins.category.generic as gen

class GenMetascan(gen.GenericCat):
    """MetaScan Online plugin code."""

    def __init__(self):
        """Initialize the plugin."""
        self.api_key = None
        gen.GenericCat.__init__(self)

    def retrieve(self, sha256):
        """
           Retrieve results for this hash from Metascan Online.
        """

        log = logging.getLogger('Mastiff.Plugins.' + self.name + '.retrieve')

        url = "https://hashlookup.metascan-online.com/v2/hash/" + sha256
        headers = { 'apikey' : self.api_key}

        # set up request
        log.debug('Submitting request to Metascan Online.')

        try:
            req = urllib2.Request(url, headers=headers)
            response = urllib2.urlopen(req, timeout=30)
        except urllib2.HTTPError, err:
            log.error('Unable to contact URL: %s', err)
            return None
        except urllib2.URLError, err:
            log.error('Unable to open connection: %s', err)
            return None
        except socket.timeout, err:
            log.error('Timeout when contacting URL: %s', err)
            return None
        except:
            log.error('Unknown Error when opening connection.')
            return None

        json = response.read()
        try:
            response_dict = simplejson.loads(json)
        except simplejson.decoder.JSONDecodeError:
            log.error('Error in Metascan Online JSON response. Are you submitting too fast?')
            return None
        else:
            log.debug('Response received.')
            return response_dict

    def submit(self, config, filename):
        """
            Submit a file to Metascan Online for analysis.

            Note: This function will likely fail if a proxy is used.
        """
        log = logging.getLogger('Mastiff.Plugins.' + self.name + '.submit')

        try:
            outdir = config.get_var('Dir', 'log_dir')
            mo_file = open(outdir + os.sep + 'metascan-online.txt', 'w')
        except IOError, err:
            log.error('Unable to open %s for writing: %s',
                      outdir + 'metascan-online.txt', err)
            return False

        # make sure we are allowed to submit
        if config.get_bvar(self.name, 'submit') == False:
            log.info('Submission disabled. Not sending file.')
            mo_file.write('File not submitted because submission disabled.\n')
            mo_file.close()
            return False

        log.info('File had not been analyzed by Metascan Online.')
        log.info('Sending file to Metascan Online.')

        # send file to Metascan Online
        url = "https://scan.metascan-online.com/v2/file"
        headers = { 'apikey' : self.api_key, 'filename': os.path.basename(filename)}

        try:
            req = urllib2.Request(url, headers=headers)
            file_to_send = open(filename, "rb").read()
            response = urllib2.urlopen(req, data=file_to_send, timeout=30)
            json = simplejson.loads(response.read())
        except urllib2.HTTPError, err:
            log.error('Unable to contact URL: %s', err)
            return None
        except urllib2.URLError, err:
            log.error('Unable to open connection: %s', err)
            return None
        except socket.timeout, err:
            log.error('Timeout when contacting URL: %s', err)
            return None
        except:
            log.error('Unknown Error when sending file.')
            return None

        # write to file
        mo_file.write('File uploaded and processing.\n')
        mo_file.write('Link: https://www.metascan-online.com/en/scanresult/file/%s\n' % json['data_id'])
        mo_file.close()

        return True

    def analyze(self, config, filename):
        """Analyze the file."""

        # sanity check to make sure we can run
        if self.is_activated == False:
            return False
        log = logging.getLogger('Mastiff.Plugins.' + self.name)
        log.info('Starting execution.')

        self.api_key = config.get_var(self.name, 'api_key')
        if self.api_key is None or len(self.api_key) == 0:
            log.error('No Metascan Online API Key - exiting.')
            return False

        sha256 = config.get_var('Misc', 'hashes')[2]

        response = self.retrieve(sha256)
        if response is None:
            # error occurred
            log.error('Did not get a response from Metascan Online. Exiting.')
            return False

        if sha256.upper() in response and response[sha256.upper()] == "Not Found":
            # The file has not been submitted
            self.submit(config, filename)
        else:
            # write response to file
            self.output_file(config.get_var('Dir', 'log_dir'), response)

        return True

    def output_file(self, outdir, response):
        """Format the output from Metascan Online into a file. """
        log = logging.getLogger('Mastiff.Plugins.' + self.name + 'output_file')

        try:
            mo_file = open(outdir + os.sep + 'metascan-online.txt', 'w')
        except IOError, err:
            log.error('Unable to open %s for writing: %s',
                      outdir + 'metascan-online.txt', err)
            return False

        out_str = ''
        result_str = ''

        out_str += 'Metascan Online Results for %s\n' % response['file_info']['md5']
        out_str += 'Last scan date: %s\n' % response['scan_results']['start_time']

        foundAV = 0

        if response['scan_results']['scan_all_result_i'] > 0:
            result_str += '{0:22} {1:24} {2:40}\n'.format('AV', 'Version', 'Results')

            for av_key in sorted(response['scan_results']['scan_details'].keys(), key=lambda s: s.lower()):

                # scan_result_i should be 1-9 (10 is engine updating)
                if 10 > response['scan_results']['scan_details'][av_key]['scan_result_i'] > 0 :
                    threat_name = response['scan_results']['scan_details'][av_key]['threat_found'].encode('utf-8')
                    if threat_name == u'':
                        threat_name = u'Unknown Threat'

                    result_str += '{0:22} {1:24} {2:40}\n'.format(av_key, \
                                             response['scan_results']['scan_details'][av_key]['def_time'], \
                                             threat_name)
                    foundAV += 1

        out_str += 'Total positive results: %d/%d\n' % (foundAV, response['scan_results']['total_avs'])
        out_str += 'Link to metascan-online.com:\nhttps://www.metascan-online.com/en/scanresult/file/%s\n\n' % response['data_id']

        mo_file.write(out_str)
        mo_file.write(result_str)

        mo_file.close()
        return True


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
   This file contains a number of helper functions for misc. tasks
   the plug-ins may want to use.
"""

__version__ = "$Id$"

import httplib, mimetypes
import binascii

"""
    The following are taken from
    http://code.activestate.com/recipes/146306/
    and are used to allow the uploading of files to multipart forms.
"""
def post_multipart(host, method, selector, fields, files):
    """
    Post fields and files to an http host as multipart/form-data.
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return the server's response page.
    """
    content_type, body = encode_multipart_formdata(fields, files)
    if method.startswith('https') is True:
        h = httplib.HTTPSConnection(host)
    else:
        h = httplib.HTTP(host)
        
    h.putrequest('POST', selector)
    h.putheader("User-Agent", 'MASTIFF Statis Analysis Framework')
    h.putheader('Content-Type', content_type)
    h.putheader('Content-Length', str(len(body)))
    h.endheaders()
    h.send(body)
    myresponse = h.getresponse().read()
    return myresponse

def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = '----------MASTIFF_STATIC_ANALYSIS_FRAMEWORK$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def get_content_type(filename):
    """ Returns MIME type for the file. """
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

def bin2hex(data):
    """
        Goes through data and turns any binary characters into its hex
        equivalent.
    """

    hexstring = ''
    for letter in data:
        if ord(letter) <= 31 or ord(letter) >= 127:
            hexstring += '\\x' + binascii.hexlify(letter)
        else:
            hexstring += letter

    return hexstring

def printable_str(string):
    """ Helper function to convert non-printable chars to its ASCII format """

    new_str = ''
    for char in string:
        if ord(char) >= 32 and ord(char) <= 126:
            new_str = new_str + char
        else:
            new_str = new_str + (r'\x%02x' % ord(char))

    return new_str


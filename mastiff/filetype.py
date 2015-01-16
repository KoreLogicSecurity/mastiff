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
File Type Analysis Functions

The functions within this module provide the functionality to help determine
the type of file given to it.

This module now supports the use of two different type of libmagic Python libraries:
- The libmagic Python library maintained with file (ftp://ftp.astron.com/pub/file/).
  This is the version installed via most Debian-based repositories.
- ahupp's python-magic repostitory installed via pip.
  (https://github.com/ahupp/python-magic)

"""

__version__ = "$Id$"

import magic
import logging
import subprocess
import re
import os

try:
    import yara
except ImportError, error:
    print "Could not import yara: %s" % error

def get_magic(file_name):
    """ Determine the file type of a given file based on its magic result."""

    log = logging.getLogger('Mastiff.FileType.Magic')
    
    try:
        # try to use magic from the file source code
        magic_ = magic.open(magic.MAGIC_NONE)
        magic_.load()
        try:
            file_type = magic_.file(file_name)
        except:
            log.error('Could not determine magic file type.')
            return None
        magic_.close()
    except AttributeError:
        # Now we are trying ahupps magic library
        try:
            file_type = magic.from_file(file_name)
        except AttributeError:
            log.error('No valid magic libraries installed.')
            return None
        except MagicException:
            log.error('Cound not determing magic file type.')
            return None        

    log.debug('Magic file type is "%s"', file_type)

    return file_type

def get_trid(file_name, trid, trid_db):
    """ DEPRECATED DO NOT USE
        TrID is a file identification tool created by Marco Pontello.
        Unfortunately, TrID does not have a Linux library we can use, so we
        will run the program and store its results.

        file_name: file to analyze
        trid = path to trid binary
        trid_db = path to trid database

        Returns a list of the hits from TrID. Each item of the returned list
        will contain a list with [ percentage, description ]
    """

    log = logging.getLogger('Mastiff.FileType.TrID')
    pattern = '^\s*([0-9\.]+)\% \([\w\.]+\) ([\S\s]+) \([0-9\/]+\)$'
    results = list()

    # if files don't exist, return empty list
    if not os.path.isfile(trid) or not os.path.isfile(trid_db):
        log.warning('TrID cannot be found. Skipping TrID file type detection.')
        return results

    trid_db = '-d:' + trid_db

    # TrID has a bug in it where it can't open a file it it begins with "./"
    # remove that
    if file_name.startswith('./'):
        file_name = file_name[2:]

    try:
        run = subprocess.Popen([trid] + [trid_db] + [file_name],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               close_fds=True)
    except subprocess.CalledProcessError, err:
        log.error('Could not run TrID: %s', err)
        return results
    except OSError,  err:
        log.error('Could not run TrID: %s',  err)
        return results    

    (output, error) = run.communicate()
    if error is not None and len(error) > 0:
        log.error('Error running TrID: %s' % error)
        return results
            
    data = [ re.match(pattern, line) for line in output.split('\n') ]

    # create a list of hits
    # each item in results will be [ percentage, description ]
    results = [ [float(match.group(1)), match.group(2)] \
                for match in data \
                if match is not None ]

    log.debug('TrID types are: %s', results)

    return results

def yara_typecheck(filename, yara_rule):
    """ Check for file type based on yara rule.
         Returns True if found, False otherwise.
    """

    if yara_rule is None:
        return False
        
    try:
        rules = yara.compile(source=yara_rule)
        matches = rules.match(filename, timeout=10)
    except:
        print "Error attempting to perform Yara filetype."
        return False
            
    if len(matches) > 0:
        return True
        
    return False

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        print get_magic(sys.argv[1])


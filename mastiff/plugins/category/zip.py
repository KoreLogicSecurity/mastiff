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
Zip File Category Plugin

File Type: Zip Archive
Purpose:
  This file contains the category class to analyze Zip archives.
Output:
   None

"""

__version__ = "$Id$"

import zipfile
import mastiff.plugins.category.categories as categories
import mastiff.filetype as FileType

class ZipCat(categories.MastiffPlugin):
    """ Category class for Zip documents."""

    def __init__(self, name=None):
        """Initialize the category."""
        categories.MastiffPlugin.__init__(self, name)

        self.cat_name = 'ZIP'
        self.my_types = [ 'Zip archive', 'ZIP compressed archive' ]
        self.yara_filetype = """rule iszip {
	    condition:
		    uint32(0x0) == 0x04034b50
        }"""

    def is_my_filetype(self, id_dict, file_name):
        """Determine if the magic string is appropriate for this category"""

        # Use the python library first
        try:
            # there are times where is_zipfile returns true for non-zipfiles
            # so we have to try and open it as well
            if zipfile.is_zipfile(file_name) is True:
                return self.cat_name
        except:
            return None

        # check magic string next
        try:
            if [ type_ for type_ in self.my_types if type_ in id_dict['magic']]:
                return self.cat_name
        except TypeError:
            return None

        # run Yara type check
        if FileType.yara_typecheck(file_name, self.yara_filetype) is True:
            return self.cat_name

        return None


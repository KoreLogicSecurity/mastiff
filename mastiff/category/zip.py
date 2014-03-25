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
import mastiff.category.categories as categories

class ZipCat(categories.MastiffPlugin):
    """ Category class for Zip documents."""

    def __init__(self, name=None):
        """Initialize the category."""
        categories.MastiffPlugin.__init__(self, name)

        self.cat_name = 'ZIP'
        self.my_types = [ 'Zip archive', 'ZIP compressed archive' ]

    def is_my_filetype(self, id_dict, file_name):
        """Determine if the magic string is appropriate for this category"""

        # Use the python library first
        if zipfile.is_zipfile(file_name) is True:
            return self.cat_name

        # check magic string next
        if [ type_ for type_ in self.my_types if type_ in id_dict['magic']]:
            return self.cat_name

        # check TrID output
        for (percent, desc) in id_dict['trid']:
            for type_ in self.my_types:
                if type_ in desc and percent > 75:
                    return self.cat_name

        return None


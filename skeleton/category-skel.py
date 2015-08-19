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
Category Skeleton Plugin

File Type: New File Type
Purpose:
  This file contains the skeleton code for a new category class to analyze
  a new file type.

Output:
   None

__init__(): MANDATORY: Any initialization code the category requires. It must
            also call the __init__ for its superclass - in this case OfficeCat.
"""

__version__ = "$Id$"

import mastiff.plugins.category.categories as categories
import mastiff.filetype as FileType

# Change the class name to identify the new file type
class SkelCat(categories.MastiffPlugin):
    """ Category class for Word documents."""

    def __init__(self, name=None):
        """Initialize the category."""
        categories.MastiffPlugin.__init__(self, name)

        # cat_name should be a one word description of the file type
        self.cat_name = 'SkelCat'
        # Add in strings from libmagic and TrID output
        self.my_types = [ 'libmagic string', 'TrID string' ]
        # Add in the Yara rule
        self.yara_filetype = """rule istype { } """

    def is_my_filetype(self, id_dict, file_name):
        """Determine if the magic string is appropriate for this category"""

        # check magic string first
        try:
            if [ type_ for type_ in self.my_types if type_ in id_dict['magic']]:
                return self.cat_name
        except:
            return None
        
        # run Yara type check
        if FileType.yara_typecheck(file_name, self.yara_filetype) is True:
            return self.cat_name

        # check TrID output, if available
        # this can likely be removed
        for (percent, desc) in id_dict['trid']:
            for type_ in self.my_types:
                # make sure percent is high enough and trid string matches
                if type_ in desc and percent > 50:
                    return self.cat_name

        # add your own code on additional file type determination here        

        return None


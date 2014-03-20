#!/usr/bin/env python
"""
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

import mastiff.category.categories as categories

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

    def is_my_filetype(self, id_dict, file_name):
        """Determine if the magic string is appropriate for this category"""

        # check magic string first
        if [ type_ for type_ in self.my_types if type_ in id_dict['magic']]:
            return self.cat_name

        # check TrID output
        for (percent, desc) in id_dict['trid']:
            for type_ in self.my_types:
                # make sure percent is high enough and trid string matches
                if type_ in desc and percent > 50:
                    return self.cat_name

        # add your own code on additional file type determination here        

        return None


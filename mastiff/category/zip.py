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
Zip File Category Plugin

File Type: Zip Archive
Purpose:
  This file contains the category class to analyze Zip archives.
Output:
   None

"""

__version__ = "$Id: zip.py,v 1.7 2013/02/11 19:55:22 thudak Exp $"

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


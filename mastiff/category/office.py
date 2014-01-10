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
Microsoft Office File Category Plugin

File Type: Microsoft Office Documents
Purpose:
  This file contains the code for the category class "office", which
  allows plugins to be created to be run on Microsoft Office documents.

Output:
   None

__init__(): MANDATORY: Any initialization code the category requires. It must
            also call the __init__ for the MastiffPlugin class.
"""

__version__ = "$Id: office.py,v 1.3 2012/06/29 16:41:56 thudak Exp $"

import mastiff.category.categories as categories

class OfficeCat(categories.MastiffPlugin):
    """Category class for Microsoft Office files."""

    def __init__(self, name=None):
        """Initialize the category."""
        categories.MastiffPlugin.__init__(self, name)
        self.cat_name = 'Office'
        self.my_types = [ 'CDF V2 Document', # PPT, DOC, XLS
                         'Composite Document File V2',
                          'Microsoft Word',
                          'Microsoft Office Word',
                          'Microsoft Excel',
                          'Microsoft PowerPoint',
                          'Microsoft Office Document'
                          ]

    def is_my_filetype(self, id_dict, file_name):
        """Determine if magic string is appropriate for this category."""

        if [ type_ for type_ in self.my_types if type_ in id_dict['magic']]:
            return self.cat_name

        # check TrID output
        for (percent, desc) in id_dict['trid']:
            for type_ in self.my_types:
                # make sure percent is high enough and trid string matches
                # 30% appears to be a good line for Office documents
                if type_ in desc and percent > 30:
                    return self.cat_name

        # May do more here with the filename...perhaps check the extension?
        return None


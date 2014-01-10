#!/bin/bash

# $Id: import-test.sh,v 1.2 2013/04/12 18:28:23 thudak Exp $
#
# Find all imports from the MASTIFF python files and ensure they can be
# imported.
#
# $1 = directory to test

if [ $# -eq 0  ] ; then
  echo "Need a directory to scan."
  exit
elif [ ! -d $1 ] ; then
  echo "$1 is not a directory."
  exit
fi

PWD=`pwd`
SAVEIFS=$IFS
IFS=$(echo -en "\n\b")

echo "Checking Python imports in $1 and below."
echo

cd $1
for FILE in `find . -name "*.py"`; do
  for IMPORT in `egrep "^\s*import\s+|^\s*from \S+ import" ${FILE} | sed -e 's/^[ \t]*//' | sort -u`; do
  ERROR=`python -c "${IMPORT}" 2>&1 | grep "ImportError" | grep -vi disitool`
  if [ $? -ne 1 ]; then
    echo ERROR: ${FILE}: ${ERROR}
  fi
done; done

cd ${PWD}
IFS=${SAVEIFS}

echo
echo "Done checking imports."
echo

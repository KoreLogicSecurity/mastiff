#!/bin/bash

MASCMD="python ./mas.py -c ./mastiff.conf -V "

# Test mastiff by running it against various file types.
# $1 = file type
# $2 = file to test
# $3 = outfile
mas_test()
{
    echo -n "Testing ${1}: "
    if [ ! -f $2 ] ; then
        echo "$2 missing. Unable to test."
        return 0
    fi

    ${MASCMD} ${2} > ${3} 2>&1
    if [ $? -ne 0 ] ; then
        OUTMSG="Failed. See ${3} for details."
    else
        OUTMSG="Success."
    fi
    echo $OUTMSG
}
    
echo "Checking for MASTIFF functionality."
echo

mas_test EXE tests/test.exe tests/test-EXE.txt
mas_test Office tests/test.doc tests/test-DOC.txt
mas_test PDF tests/test.pdf tests/test-PDF.txt
mas_test ZIP tests/test.zip tests/test-ZIP.txt

echo
echo "Done checking MASTIFF functionality."

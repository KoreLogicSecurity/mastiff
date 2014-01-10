# $Id: Makefile,v 1.15 2013/04/12 18:28:23 thudak Exp $
#
# Makefile for installation of mastiff.
#

all: build

build::
	@ python setup.py build

check test:
	@ bash tests/import-test.sh `pwd`
	@ bash tests/mastiff-test.sh
	@ rm -rf work/

check-clean test-clean: clean
	@ rm -f tests/test-*.txt

clean:
	@ rm -f `find . -name "*.pyc" -o -name "*~"`
	@ rm -rf dist build mastiff.egg-info
	@ rm -f tests/*.txt

clean-all: check-clean dev-clean

dev:
	@ python setup.py develop

dev-clean: clean
	@ python setup.py develop --uninstall
	@ rm -f /usr/local/bin/mas.py

dist sdist::
	@ python setup.py sdist

install: build
	@ python setup.py install

lint:
	@ find . -name "*.py" -exec pylint --rcfile=pylint.rc {} \;

sign: dist
	@ version_number=`egrep '^version = 0x' mastiff/__init__.py | awk '{print $$3}'` ; \
	version_string=`utils/version2string -t tar -v $${version_number}` ; \
	dist_file="dist/mastiff-$${version_string}.tar.gz" ; \
	gpg --default-key 64615D14 -s -b $${dist_file}


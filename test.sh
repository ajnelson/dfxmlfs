#!/bin/bash

set -e
set -x

if [ ! -d testdir ]; then
  mkdir testdir
fi

#Debug implies foreground mode, so sleep to allow mount to finish before using directory.
python2.7 dfxmlfs.py -d -o xmlfile=test.xml testdir >stdout.log 2>stderr.log &
sleep 1

ls testdir
ls -a testdir
ls -la testdir
find testdir | sort

./cleanup.sh

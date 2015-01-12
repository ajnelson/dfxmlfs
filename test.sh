#!/bin/bash

set -e
set -x

if [ ! -d testdir ]; then
  mkdir testdir
fi

#Debug implies foreground mode, so sleep to allow mount to finish before using directory.
python dfxmlfs-hello.py -d testdir >stdout.log 2>stderr.log & #-o xmlfile=test.xml 
sleep 1

ls testdir

./cleanup.sh

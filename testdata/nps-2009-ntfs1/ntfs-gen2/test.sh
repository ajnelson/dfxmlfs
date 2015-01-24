#!/bin/bash

set -e
set -x

if [ ! -d testdir ]; then
  mkdir testdir
fi

#Debug implies foreground mode, so sleep to allow mount to finish before using directory.
python2.7 dfxmlfs.py \
  -d \
  -o xmlfile=ntfs1-gen2.E01.dfxml \
  -o imgfile=ntfs1-gen2.E01 \
  testdir \
  >stdout.log 2>stderr.log &
sleep 1

#Disable halt-on-errors here to allow cleanup script to run.
set +e

python test_reads.py --debug ntfs1-gen2.E01.dfxml testdir
rc=$?

./cleanup.sh
sleep 1

exit $rc

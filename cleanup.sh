#!/bin/bash

set -x

if [ "x$(which fusermount)" == "x" ]; then
  umount testdir
else
  fusermount -u testdir 
fi

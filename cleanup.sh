#!/bin/bash

set -x

fusermount -u testdir || umount testdir

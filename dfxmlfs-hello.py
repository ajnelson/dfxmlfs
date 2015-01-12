#!/usr/bin/env python

#    Copyright (C) 2006  Andrew Straw  <strawman@astraw.com>
#
#    This program can be distributed under the terms of the GNU LGPL.
#    See the file COPYING.
#

import os
import stat
import errno
import logging

import fuse

import Objects

_logger = logging.getLogger(os.path.basename(__file__))

if not hasattr(fuse, '__version__'):
    raise RuntimeError, \
        "your fuse-py doesn't know of fuse.__version__, probably it's too old."

fuse.fuse_python_api = (0, 2)

hello_path = '/hello'
hello_str = 'Hello World!\n'

class MyStat(fuse.Stat):
    def __init__(self):
        self.st_mode = 0
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 0
        self.st_uid = 0
        self.st_gid = 0
        self.st_size = 0
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0

class HelloFS(fuse.Fuse):

    def main(self):
        if not hasattr(self, "xmlfile"):
            raise RuntimeError("-o xmlfile must be passed on the command line.")

        _logger.debug("Parsing DFXML file...")
        self.objects_by_path = dict()
        for (event, obj) in Objects.iterparse(self.xmlfile):
            if not isinstance(obj, Objects.FileObject):
                continue
            _logger.debug("File: %r." % obj.filename)
            self.objects_by_path[obj.filename] = obj
        _logger.debug("Parsed DFXML file.")
        _logger.debug("self.objects_by_path = %r." % self.objects_by_path)

        return fuse.Fuse.main(self)

    def getattr(self, path):
        st = MyStat()
        if path == '/':
            st.st_mode = stat.S_IFDIR | 0755
            st.st_nlink = 2
        elif path == hello_path:
            st.st_mode = stat.S_IFREG | 0444
            st.st_nlink = 1
            st.st_size = len(hello_str)
        else:
            return -errno.ENOENT
        return st

    def readdir(self, path, offset):
        for r in  '.', '..', hello_path[1:]:
            yield fuse.Direntry(r)

    def open(self, path, flags):
        if path != hello_path:
            return -errno.ENOENT
        accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        if (flags & accmode) != os.O_RDONLY:
            return -errno.EACCES

    def read(self, path, size, offset):
        if path != hello_path:
            return -errno.ENOENT
        slen = len(hello_str)
        if offset < slen:
            if offset + size > slen:
                size = slen - offset
            buf = hello_str[offset:offset+size]
        else:
            buf = ''
        return buf

def main():
    usage="""
Userspace DFXML file system.

""" + fuse.Fuse.fusage
    server = HelloFS(version="%prog " + fuse.__version__,
                     usage=usage,
                     dash_s_do='setsingle')

    server.parser.add_option(mountopt="xmlfile", metavar="XMLFILE",
                             help="Mount this XML file")
    server.parse(values=server, errex=1)

    logging.basicConfig(level=logging.DEBUG if "debug" in server.fuse_args.optlist else logging.INFO)

    server.main()

if __name__ == '__main__':
    main()


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

def obj_to_stat(obj):
    st = fuse.Stat()

    st.st_ino = obj.inode

    st.st_dev = 0

    st.st_nlink = obj.nlink

    st.st_size = obj.filesize

    #Don't try translating user IDs for now - complicated in NTFS.
    st.st_uid = 0
    st.st_gid = 0

    if fo.name_type == "r":
        st.st_mode = 0o0444 | stat.S_IFREG
    elif fo.name_type == "d":
        st.st_mode = 0o0555 | stat.S_IFDIR
    else:
        st.st_mode = 0o0444

    if obj.atime is None:
        st.st_atime = 0
    else:
        st.st_atime = obj.atime.timestamp()

    if obj.mtime is None:
        st.st_mtime = 0
    else:
        st.st_mtime = obj.mtime.timestamp()

    if obj.crtime is None:
        st.st_ctime = 0
    else:
        st.st_ctime = obj.crtime.timestamp()

    return st

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
        if path == '/':
            st = fuse.Stat()
            st.st_mode = stat.S_IFDIR | 0o555
            st.st_nlink = 2
        else:
            obj = self.objects_by_path.get(path)
            if obj is None:
                return -errno.ENOENT
            st = obj_to_stat(obj)
        return st

    def readdir(self, path, offset):
        for r in  '.', '..', hello_path[1:]:
            yield fuse.Direntry(r)

    def open(self, path, flags):
        #Existence check
        if path == "/":
            pass
        elif not path in self.objects_by_path:
            return -errno.ENOENT

        #Access check - read-only
        accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        if (flags & accmode) != os.O_RDONLY:
            return -errno.EACCES

        return 0

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


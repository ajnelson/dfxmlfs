#!/usr/bin/env python

#    HelloFS Copyright (C) 2006  Andrew Straw  <strawman@astraw.com>
#
#    DFXMLFS Copyright (C) 2015  Prometheus Computing, LLC.
#      Implemented by Alex Nelson <a.nelson@prometheuscomputing.com>
#
#    This program can be distributed under the terms of the GNU LGPL v2.1.
#    See the file COPYING.
#

__version__ = "0.0.1"

import os
import stat
import errno
import logging
import collections

import fuse

import Objects

_logger = logging.getLogger(os.path.basename(__file__))

if not hasattr(fuse, '__version__'):
    raise RuntimeError, \
        "your fuse-py doesn't know of fuse.__version__, probably it's too old."

fuse.fuse_python_api = (0, 2)

#This list is for debug purposes.
_stat_fields = ['st_atime', 'st_ctime', 'st_dev', 'st_gid', 'st_ino', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid']

def obj_to_stat(obj):
    st = fuse.Stat()
    #for field in _stat_fields:
    #    _logger.debug("st.%s = %r." % (field, getattr(st, field)))

    st.st_ino = obj.inode

    st.st_dev = 0

    st.st_nlink = obj.nlink or 0 #In case of None

    st.st_size = obj.filesize

    #Don't try translating user IDs for now - complicated in NTFS.
    st.st_uid = 0
    st.st_gid = 0

    if obj.name_type == "r":
        st.st_mode = 0o0444 | stat.S_IFREG
    elif obj.name_type == "d":
        st.st_mode = 0o0555 | stat.S_IFDIR
    else:
        st.st_mode = 0o0444

    #_logger.debug("Setting timestamps.")
    if obj.atime is None:
        st.st_atime = 0
    else:
        st.st_atime = obj.atime.timestamp

    #_logger.debug("Set a timestamp.")
    if obj.mtime is None:
        st.st_mtime = 0
    else:
        st.st_mtime = obj.mtime.timestamp

    if obj.crtime is None:
        st.st_ctime = 0
    else:
        st.st_ctime = obj.crtime.timestamp

    #_logger.debug("st = %r." % st)
    #for field in _stat_fields:
    #    _logger.debug("st.%s = %r." % (field, getattr(st, field)))
    return st

class DFXMLFS(fuse.Fuse):

    def __init__(self, *args, **kw):
        self._referenced_inodes = set()
        self._last_assigned_inode_number = 2

        fuse.Fuse.__init__(self, *args, **kw)

    def _next_inode_number(self):
        while self._last_assigned_inode_number < 2**32:
            self._last_assigned_inode_number += 1
            if not self._last_assigned_inode_number in self.referenced_inodes:
                break
        if self._last_assigned_inode_number == 2**32:
            raise ValueError("Out of inode numbers.")
        return self._last_assigned_inode_number

    def main(self):
        #_logger.debug("dir(self) = %r." % dir(self))

        if not hasattr(self, "imgfile"):
            self.imgfile = None
        else:
            #_logger.debug("Getting real imgfile path.")
            self.imgfile = os.path.realpath(self.imgfile)
            #_logger.debug("self.imgfile = %r." % self.imgfile)

        if not hasattr(self, "xmlfile"):
            raise RuntimeError("-o xmlfile must be passed on the command line.")

        _logger.info("Parsing DFXML file...")

        #Key: Absolute path, including partition designation
        #Value: Objects.FileObject
        self.objects_by_path = dict()

        self.dir_lists_by_path = collections.defaultdict(list)

        self.volumes = dict()

        objects_without_inode_numbers = []

        for (tup_no, (event, obj)) in enumerate(Objects.iterparse(self.xmlfile)):
            if not isinstance(obj, Objects.FileObject):
                continue
            #_logger.debug("obj.filename = %r." % obj.filename)

            alloc = obj.is_allocated()
            if alloc is None:
                #_logger.debug("Assuming allocated.")
                pass
            elif alloc == False:
                #_logger.debug("Not allocated.")
                continue
            if obj.filename is None:
                #_logger.debug("Null filename.")
                continue
            if obj.filename.endswith(("/.", "/..")) or obj.filename in [".", ".."]:
                #_logger.debug("Dot-dir filename.")
                continue

            partition_dir = "partition_" + ("null" if obj.partition is None else str(obj.partition))
            if obj.partition not in self.volumes:
                self.volumes[obj.partition] = obj.volume_object #Might be null.

            #Every file should end up with an inode number; but they should be assigned after the stream is all visited.
            if obj.inode is None:
                objects_without_inode_numbers.append(obj)

            filepath = partition_dir + "/" + obj.filename
            self.objects_by_path["/" + filepath] = obj

            basename = os.path.basename(filepath)
            dirname = os.path.dirname(filepath)

            self.dir_lists_by_path["/" + dirname].append(basename)

            #Shorten reading DFXML files in debug settings
            if "debug" in self.fuse_args.optlist and tup_no > 50:
                _logger.debug("Shortening object parsing while in debug mode: Only 50 file objects read from XML.")
                break

        #Assign inode numbers for objects that were in the stream first
        for obj in objects_without_inode_numbers:
            obj.inode = self._next_inode_number()

        #Creating the top-level partition directories a loop ago means they need to be created again for the root directory.
        for partition_number in self.volumes:
            partition_dir = "partition_" + ("null" if partition_number is None else str(partition_number))

            partition_obj = Objects.FileObject()
            partition_obj.filename = partition_dir
            partition_obj.filesize = 0
            partition_obj.name_type = "d"
            partition_obj.alloc = True
            partition_obj.inode = self._next_inode_number()
            partition_obj.nlink = 2 #This should be adjusted to be 1 + # of directory children.
            self.objects_by_path["/" + partition_dir] = partition_obj

            self.dir_lists_by_path["/"].append(partition_dir)

        _logger.info("Parsed DFXML file.")
        #_logger.debug("self.objects_by_path = %r." % self.objects_by_path)
        #_logger.debug("self.dir_lists_by_path = %r." % self.dir_lists_by_path)
        #_logger.debug("self.volumes = %r." % self.volumes)

        return fuse.Fuse.main(self)

    def getattr(self, path):
        if path == '/':
            st = fuse.Stat()
            st.st_mode = stat.S_IFDIR | 0o555
            st.st_nlink = len(self.dir_lists_by_path["/"])
        else:
            obj = self.objects_by_path.get(path)
            if obj is None:
                return -errno.ENOENT
            st = obj_to_stat(obj)
            #for field in _stat_fields:
            #    _logger.debug("st.%s = %r." % (field, getattr(st, field)))
        return st

    def readdir(self, path, offset):
        dir_list = self.dir_lists_by_path.get(path)
        if dir_list is None:
            _logger.error("readdir failed to find a directory: %r." % path)
        else:
            for r in  '.', '..':
                yield fuse.Direntry(r)
            for filename in dir_list:
                yield fuse.Direntry(filename)

    def open(self, path, flags):
        #Existence check
        #TODO Isn't this handled by getattr?
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
        _logger.debug("read(%r, %r, %r)" % (path, size, offset))
        if self.imgfile is None:
            _logger.error("Cannot read file without backing disk image.")
            return -errno.EIO

        #Existence check
        #TODO Isn't this handled by getattr?
        obj = self.objects_by_path.get(path)
        if obj is None:
            _logger.debug("Could not get file for reading: %r." % path)
            return -errno.ENOENT
        _logger.debug("Found object at path: %r." % path)

        #File type check
        if obj.name_type is None:
            #Assume regular file.
            pass
        elif obj.name_type == "d":
            return -errno.EISDIR
        #_logger.debug("File type check passed.")

        #File size check
        if obj.filesize == 0:
            return bytes()
        #_logger.debug("File size check passed.")

        #Compression awaits updates to the core DFXML library.
        if obj.compressed:
            _logger.info("Cannot currently read NTFS-compressed files.")
            return -errno.EOPNOTSUPP

        #Data addresses check
        retval = bytes()
        bytes_to_skip = offset
        bytes_to_read = size
        for buf in obj.extract_facet("content", self.imgfile):
            _logger.debug("Inspecting %d-byte buffer." % len(buf))
            if bytes_to_skip < 0:
                break

            #This is an inefficient linear scan from the beginning of the buffer.  Would be better to use the length of the byte runs, but that will mean a lot of code duplication.
            #The inefficiency here is reading from the beginning each time.
            blen = len(buf)
            if bytes_to_skip < blen:
                if bytes_to_skip + bytes_to_read > blen:
                    bytes_to_read = blen - bytes_to_skip
                #This loop will run a small number of times (read is called on 4KiB-or-so chunks), so += shouldn't be too awful for starters.
                _logger.debug("Reading bytes of buffer: [%d, %d)." % (bytes_to_skip, bytes_to_skip + bytes_to_read))
                retval += buf[bytes_to_skip:bytes_to_skip + bytes_to_read]
            bytes_to_skip -= blen

        #_logger.debug("Returning %d bytes." % len(retval))
        return retval

    @property
    def referenced_inodes(self):
        """Set of inode numbers referenced in the backing DFXML file.  Used oo inodes can be invented for virtual files."""
        return self._referenced_inodes

def main():
    usage="""
Userspace DFXML file system.

""" + fuse.Fuse.fusage
    server = DFXMLFS(version="%prog " + fuse.__version__,
                     usage=usage,
                     dash_s_do='setsingle')

    server.parser.add_option(mountopt="imgfile", metavar="IMGFILE",
                             help="Use this backing disk image file")
    server.parser.add_option(mountopt="xmlfile", metavar="XMLFILE",
                             help="Mount this XML file")
    server.parse(values=server, errex=1)

    logging.basicConfig(level=logging.DEBUG if "debug" in server.fuse_args.optlist else logging.INFO)

    server.main()

if __name__ == '__main__':
    main()

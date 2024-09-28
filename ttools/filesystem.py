#!/usr/bin/env python

#    Copyright (C) 2001  Jeff Epler  <jepler@unpythonic.dhs.org>
#    Copyright (C) 2006  Csaba Henk  <csaba.henk@creo.hu>
#
#    This program can be distributed under the terms of the GNU LGPL.
#    See the file COPYING.
#

from __future__ import print_function, annotations

import os
import sys
from errno import EACCES, EINVAL, EOPNOTSUPP

import fcntl
from threading import Lock
import fuse
from fuse import Fuse
import patoolib
import re
from textual.message import Message
import argparse

if not hasattr(fuse, "__version__"):
    raise RuntimeError(
        "your fuse-py doesn't know of fuse.__version__, probably it's too old."
    )

fuse.fuse_python_api = (0, 2)

fuse.feature_assert("stateful_files", "has_init")


def flag2mode(flags):
    md = {os.O_RDONLY: "rb", os.O_WRONLY: "wb", os.O_RDWR: "wb+"}
    m = md[flags & (os.O_RDONLY | os.O_WRONLY | os.O_RDWR)]

    if flags | os.O_APPEND:
        m = m.replace("w", "a", 1)

    return m


from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from helperfunctions import get_logger

logger = get_logger(__name__)

persistent = set()
unpacked_dir = set()
unpacked_files = set()


def _supported_formats(operations=patoolib.ArchiveCommands):
    """
    Return a list of supported archive formats for an iterable of operations.
    Patoolib doesn't support this out of the box, so here's a hack..

    :param operations: The operations to check for, defaults to ArchiveCommands.
    :type operations:  List|Tuple|Set|Dict[str]
    :return:           A list of supported archive formats.
    :rtype:            List[str]
    """
    ArchiveFormats = patoolib.ArchiveFormats

    supported = list(ArchiveFormats)
    for format in ArchiveFormats:
        # NOTE: If we wish to include supported formats in the CLI
        # argparse default nargs to an empty list, so we would need some
        # check to set operations to ArchiveCommands if bool(operations) is False.
        for command in operations:
            try:
                patoolib.find_archive_program(format, command)
            except patoolib.util.PatoolError:
                supported.remove(format)
                break
    return supported


supported_formats = _supported_formats()


class FS(Fuse):
    """
    Overlay Filesystem
    Mirrors the filesystem tree from some point on(root)
    at the mount_point

    PARAMS:
    -------
    dash_s_do: str
        Run single or multithreaded
    root: str
        Path to root of filesystem, default is '/'
    mount_point: str
        Path to mountpoint of filesystem
    nonempty: bool
        Whether to accept a nonempty root directory, default is False
    """

    class Request(Message):
        def __init__(self, requestor: object, id: int, root: str, mount_point: str):
            super().__init__()
            self.requestor: object = requestor
            self.id: int = id
            self.root: str = root
            self.mount_point: str = mount_point

    class Status:
        def __init__(self, id: int, status: bool, exception: Exception | None = None):
            self.id: int = id
            self.ok: bool = status
            self.exception: Exception | None = exception

    class Response(Message):
        def __init__(self, id: int, status: FS.Status):
            super().__init__()
            self.id: int = id
            self.status: FS.Status = status

    def __init__(self, *args, **kw):
        self.root = kw.pop("root", "/")
        self.mount_point = kw["mountpoint"]
        sys.argv = sys.argv[:1] + [kw.pop("mountpoint"), "-o", "root=" + self.root]
        if kw.pop("nonempty", False):
            sys.argv.append("-o")
            sys.argv.append("nonempty")
        logger.debug(sys.argv)
        logger.debug(args)
        args = ()
        logger.debug(kw)
        logger.debug("Init Fuse")
        Fuse.__init__(self, *args, **kw)
        logger.debug("walk existing fs")
        self.walk_fs()
        logger.debug("Init done")
        # self.root = kw.pop("root", ".")
        # self.mount_point = kw.pop("mountpoint")
        # sys.argv = [self.mount_point, "-o", "root=" + self.root]
        # if kw.pop("nonempty", False):
        #     sys.argv.append("-o")
        #     sys.argv.append("nonempty")
        # Fuse.__init__(self, *args, **kw)
        # self.walk_fs()

    def walk_fs(self):
        """
        Persist any files/folders that exists at the time of mounting.
        """
        relative_root = "./"
        for root, dirs, files in os.walk(self.root):
            logger.debug(f"{root} : {dirs} : {files}")
            for d in dirs:
                persistent.add(os.path.join(relative_root, d))
            for f in files:
                persistent.add(os.path.join(relative_root, f))
        logger.debug(f"Done walking: {self.root}")

    def getattr(self, path):
        return os.lstat("." + path)

    def readlink(self, path):
        return os.readlink("." + path)

    def readdir(self, path, offset):
        for e in os.listdir("." + path) + [".", ".."]:
            yield fuse.Direntry(e)

    def unlink(self, path):
        global unpacked
        global persistent
        path = "." + path
        try:
            unpacked_files.remove(path)
        except KeyError as ke:
            pass
        try:
            persistent.remove(path)
        except KeyError as ke:
            pass
        os.unlink(path)

    def rmdir(self, path):
        path = "." + path
        try:
            unpacked_dir.remove(path)
        except KeyError as ke:
            pass
        try:
            persistent.remove(path)
        except KeyError as ke:
            pass
        os.rmdir(path)

    def symlink(self, path, path1):
        os.symlink(path, "." + path1)

    def rename(self, path, path1):
        os.rename("." + path, "." + path1)

    def link(self, path, path1):
        os.link("." + path, "." + path1)

    def chmod(self, path, mode):
        os.chmod("." + path, mode)

    def chown(self, path, user, group):
        os.chown("." + path, user, group)

    def truncate(self, path, len):
        f = open("." + path, "a")
        f.truncate(len)
        f.close()

    def mknod(self, path, mode, dev):
        os.mknod("." + path, mode, dev)

    def mkdir(self, path, mode):
        persistent.add("." + path)
        os.mkdir("." + path, mode)

    def utime(self, path, times):
        os.utime("." + path, times)

    def access(self, path, mode):
        if not os.access("." + path, mode):
            return -EACCES

    def statfs(self):
        """
        Should return an object with statvfs attributes (f_bsize, f_frsize...).
        Eg., the return value of os.statvfs() is such a thing (since py 2.2).
        If you are not reusing an existing statvfs object, start with
        fuse.StatVFS(), and define the attributes.

        To provide usable information (i.e., you want sensible df(1)
        output, you are suggested to specify the following attributes:

            - f_bsize - preferred size of file blocks, in bytes
            - f_frsize - fundamental size of file blcoks, in bytes
                [if you have no idea, use the same as blocksize]
            - f_blocks - total number of blocks in the filesystem
            - f_bfree - number of free blocks
            - f_files - total number of file inodes
            - f_ffree - nunber of free file inodes
        """
        return os.statvfs(".")

    def fsinit(self):
        os.chdir(self.root)

    def cleanup(self):
        global unpacked
        for path in unpacked_files:
            try:
                os.remove(path)
            except FileNotFoundError as fnfe:
                continue
            except OSError as oe:
                logger.exception(oe)
                continue
            except Exception as e:
                logger.exception(e)
                continue
        for path in unpacked_dir:
            try:
                os.removedirs(path)
            except FileNotFoundError:
                continue
            except OSError as oe:
                logger.exception(oe)
                continue
            except Exception as e:
                logger.exception(e)
                continue
        logger.debug("Cleaned up")

    def run(self):
        logger.debug("Running FS")
        retval = 0
        try:
            self.parser.add_option(
                mountopt="root",
                metavar="PATH",
                default=f"{os.getcwd()}",
                help="Root directory to mount",
            )
            self.parse(values=self, errex=1)
            if self.fuse_args.mount_expected():
                os.makedirs(self.root, exist_ok=True)
                os.makedirs(self.mount_point, exist_ok=True)
            self.file_class = self.File
            retval = Fuse.main(self)
        except OSError as OSE:
            logger.exception(OSE)
            sys.exit(1)
        except Exception as e:
            logger.exception(e)
        finally:
            self.cleanup()
            return retval

    class File(object):
        """
        File object that redirects all operations to an underlying file
        """

        def _extract_archive(self, path: str) -> None:
            global persistent
            # Force relative path, input path is assumed absolute in our newly mounted fs
            # but this is not the same as the path on the host system
            path = "." + path if not path.startswith(".") else path
            out_path = re.sub(r"\.[a-zA-Z0-9]*$", "", path)
            os.makedirs(out_path, exist_ok=True)
            try:
                old_files = persistent.copy()
                patoolib.extract_archive(path, outdir=out_path)
                # patoolib creates some temp files that we do not want to keep.
                persistent = old_files
                for path, dirs, files in os.walk(out_path):
                    for d in dirs:
                        unpacked_dir.add(os.path.join(path, d))
                    for f in files:
                        unpacked_files.add(os.path.join(path, f))
            except patoolib.util.PatoolError as archE:
                logger.exception(archE)
                os.removedirs(out_path)
                return
            unpacked_dir.add(out_path)

        def __init__(self, path: str, flags, *mode):
            archive_type = re.search(r"[a-zA-Z0-9]*$", path)
            archive_type = archive_type.group(0) if archive_type else None
            try:
                if archive_type in supported_formats:
                    self._extract_archive(path)
                else:
                    persistent.add("." + path)
            except Exception as e:
                logger.exception(e)
            self.file = os.fdopen(os.open("." + path, flags, *mode), flag2mode(flags))
            self.fd = self.file.fileno()
            if hasattr(os, "pread"):
                self.iolock = None
            else:
                self.iolock = Lock()

        def read(self, length, offset):
            if self.iolock:
                self.iolock.acquire()
                try:
                    self.file.seek(offset)
                    return self.file.read(length)
                finally:
                    self.iolock.release()
            else:
                return os.pread(self.fd, length, offset)

        def write(self, buf, offset):
            if self.iolock:
                self.iolock.acquire()
                try:
                    self.file.seek(offset)
                    self.file.write(buf)
                    return len(buf)
                finally:
                    self.iolock.release()
            else:
                return os.pwrite(self.fd, buf, offset)

        def release(self, flags):
            self.file.close()

        def _fflush(self):
            if "w" in self.file.mode or "a" in self.file.mode:
                self.file.flush()

        def fsync(self, isfsyncfile):
            self._fflush()
            if isfsyncfile and hasattr(os, "fdatasync"):
                os.fdatasync(self.fd)
            else:
                os.fsync(self.fd)

        def flush(self):
            self._fflush()
            os.close(os.dup(self.fd))

        def fgetattr(self):
            return os.fstat(self.fd)

        def ftruncate(self, len):
            self.file.truncate(len)

        def lock(self, cmd, owner, **kw):
            op = {
                fcntl.F_UNLCK: fcntl.LOCK_UN,
                fcntl.F_RDLCK: fcntl.LOCK_SH,
                fcntl.F_WRLCK: fcntl.LOCK_EX,
            }[kw["l_type"]]
            if cmd == fcntl.F_GETLK:
                return -EOPNOTSUPP
            elif cmd == fcntl.F_SETLK:
                if op != fcntl.LOCK_UN:
                    op |= fcntl.LOCK_NB
            elif cmd == fcntl.F_SETLKW:
                pass
            else:
                return -EINVAL

            fcntl.lockf(self.fd, op, kw["l_start"], kw["l_len"])


# def main():
#     FS(
#         dash_s_do="whine",
#         root="/",
#     ).run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mount a filesystem")
    parser.add_argument(
        "--root",
        type=str,
        default=os.getcwd(),
        help="Root directory to mount",
    )
    parser.add_argument(
        "--mountpoint",
        type=str,
        default=".mnt",
        help="Mountpoint of the filesystem",
    )
    parser.add_argument(
        "--nonempty",
        action="store_true",
        help="Allow mounting over non-empty directory",
        required=False,
        default=False,
    )
    args = parser.parse_args()
    FS(
        dash_s_do="whine",
        root=args.root,
        mountpoint=args.mountpoint,
        nonempty=args.nonempty,
    ).run()

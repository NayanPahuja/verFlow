import argparse
import os
import collections
import configparser
import sys
from datetime import datetime
import grp, pwd
from fnmatch import fnmatch
import hashlib
from math import ceil
import re
import zlib

from verFlowRepository import repoFile


class vfIndexEntry (object):
    def __init__(self,ctime = None, mtime = None, dev = None, ino = None,
                 mode_type = None,mode_perms = None, uid = None, gid = None,
                 fsize = None, sha = None, flag_assume_valid = None,
                 flag_stage = None, name = None):
      # The last time a file's metadata changed.  This is a pair
      # (timestamp in seconds, nanoseconds)
      self.ctime = ctime
      # The last time a file's data changed.  This is a pair
      # (timestamp in seconds, nanoseconds)
      self.mtime = mtime
      # The ID of device containing this file
      self.dev = dev
      # The file's inode number
      self.ino = ino
      # The object type, either b1000 (regular), b1010 (symlink),
      # b1110 (gitlink).
      self.mode_type = mode_type
      # The object permissions, an integer.
      self.mode_perms = mode_perms
      # User ID of owner
      self.uid = uid
      # Group ID of ownner
      self.gid = gid
      # Size of this object, in bytes
      self.fsize = fsize
      # The object's SHA
      self.sha = sha
      self.flag_assume_valid = flag_assume_valid
      self.flag_stage = flag_stage
      # Name of the object (full path this time!)
      self.name = name

    
class vfIndex (object):
   version = None
   entries = []

   #ext = None
   #sha = None

   def __init__(self, version = 2, entries = None) -> None:
      
      if not entries:
         entries = list()

      self.version = version
      self.entries = entries



def indexRead(repo):
   """Reads the index file of the given repository"""
   #Get the index file from the repository
   index_file_path = repoFile(repo, "index")

    # A new repo won't have an index file
   if not os.path.exists(index_file_path):
       return vfIndex()
    # Read the contents of the file
   with open(index_file_path, 'rb') as f:
       raw = f.read()

   header = raw[:12]
   signature = header[:4]
   assert  signature == b"DIRC" #stands for Dir Cache
   version = int.from_bytes(header[4:8],"big")
   assert version == 2, "verflow currently only supports index file version 2"
   count = int.from_bytes(header[8:12],"big")

   entries = list()
   # content of the index file
   content = raw[12:]
   idx = 0

   for i in range(0,count):
        # Read creation time, as a unix timestamp (seconds since
        # 1970-01-01 00:00:00, the "epoch")

      ctime_s =  int.from_bytes(content[idx: idx+4], "big")
        # Read creation time, as nanoseconds after that timestamps,
        # for extra precision.
      ctime_ns = int.from_bytes(content[idx+4: idx+8], "big")

        # Same for modification time: first seconds from epoch.

      mtime_s = int.from_bytes(content[idx+8 : idx + 12], "big")
        # Then extra nanoseconds
      mtime_ns = int.from_bytes(content[idx+12 : idx + 16], "big")

        # Device ID
      dev = int.from_bytes(content[idx+16 : idx + 20], "big")
        # Inode
      ino = int.from_bytes(content[idx+20: idx+24], "big")
        # Ignored.
      unused = int.from_bytes(content[idx+24: idx+26], "big")

      assert 0 == unused

      mode = int.from_bytes(content[idx+26: idx+28], "big")

      mode_type = mode >> 12

        #validate mode is one of the possible modes
        
      assert mode_type in [0b1000, 0b1010, 0b1110]

      mode_perms = mode & 0b0000000111111111

        # user ID
      uid = int.from_bytes(content[idx+28 : idx+32],"big")

        #group ID
      gid = int.from_bytes(content[idx+32 : idx+36],"big")

        #File Size
      fsize = int.from_bytes(content[idx+36 : idx + 40],"big")

        #SHA (object ID) Store it as lowercase hex for consistency accross source code
      sha = format(int.from_bytes(content[idx+40 : idx+60],"big"),"040x")

        #Flags ? Ignore for now
      flags = int.from_bytes(content[idx+60 : idx+62],"big")

        #Parse Flags
      flag_assume_valid = (flags & 0b1000000000000000) != 0
      flag_extended = (flags & 0b0100000000000000) != 0

      assert not flag_extended

      flag_stage = flags & 0b0011000000000000

        # Length of the name.  This is stored on 12 bits, some max
        # value is 0xFFF, 4095.  Since names can occasionally go
        # beyond that length, git treats 0xFFF as meaning at least
        # 0xFFF, and looks for the final 0x00 to find the end of the
        # name --- at a small, and probably very rare, performance
        # cost.

      name_length = flags & 0b0000111111111111

        #We've read 62 bytes so far from index file

      idx+=62
      if name_length < 0xFFF:
         assert content[idx+name_length] == 0x00
         raw_name = content[idx : idx + name_length]
         idx += name_length + 1
      else:
         print("Notice: Name is 0x{:X} bytes long.".format(name_length))
            # This probably wasn't tested enough.  It works with a
            # path of exactly 0xFFF bytes.  Any extra bytes broke
            # something between git, my shell and my filesystem.
         null_idx = content.find(b'\x00', idx + 0xFFF)
         raw_name = content[idx: null_idx]
         idx = null_idx + 1

      # Just parse the name as utf8
      name = raw_name.decode("utf8")
      # Data is padded on multiples of eight bytes for pointer
      # alignment, so we skip as many bytes as we need for the next
      # read to start at the right position.

      idx = 8 * ceil(idx/8)

      entries.append(vfIndexEntry(ctime=(ctime_s, ctime_ns),
                                     mtime=(mtime_s,  mtime_ns),
                                     dev=dev,
                                     ino=ino,
                                     mode_type=mode_type,
                                     mode_perms=mode_perms,
                                     uid=uid,
                                     gid=gid,
                                     fsize=fsize,
                                     sha=sha,
                                     flag_assume_valid=flag_assume_valid,
                                     flag_stage=flag_stage,
                                     name=name))
      
   return vfIndex(version = version, entries = entries)


def indexWrite(repo, index):
    with open(repoFile(repo, "index"), "wb") as f:
        # HEADER
        # TYPE
        f.write(b"DIRC")
        
        # VERSION
        f.write(index.version.to_bytes(4, "big"))
        
        # Write the number of entries.
        f.write(len(index.entries).to_bytes(4, "big"))

        # ENTRIES
        idx = 0
        for e in index.entries:
            f.write(e.ctime[0].to_bytes(4, "big"))
            f.write(e.ctime[1].to_bytes(4, "big"))
            f.write(e.mtime[0].to_bytes(4, "big"))
            f.write(e.mtime[1].to_bytes(4, "big"))
            f.write(e.dev.to_bytes(4, "big"))
            f.write(e.ino.to_bytes(4, "big"))
            
            # MODE
            mode = (e.mode_type << 12) | e.mode_perms
            f.write(mode.to_bytes(4, "big"))
            
            # UID
            f.write(e.uid.to_bytes(4, "big"))
            
            # GID
            f.write(e.gid.to_bytes(4, "big"))
            
            # FILE SIZE
            f.write(e.fsize.to_bytes(4, "big"))
            
            # SHA
            f.write(int(e.sha, 16).to_bytes(20, "big"))
            
            # FLAGS
            flag_assume_valid = 0x1 << 15 if e.flag_assume_valid else 0
            name_bytes = e.name.encode("utf8")
            bytes_len = len(name_bytes)
            if bytes_len > 0xFFF:
                name_length = 0xFFF
            else:
                name_length = bytes_len
            
            # FLAGS - write the flags field
            flags = (flag_assume_valid | e.flag_stage | name_length) & 0xFFFF
            f.write(flags.to_bytes(2, "big"))
            
            # Write the name
            f.write(name_bytes)
            f.write((0).to_bytes(1, "big"))
            
            idx += 62 + len(name_bytes) + 1
            # Null bytes padding to ensure that the entry is a multiple of 8 bytes
            if idx % 8 != 0:
              pad = 8 - (idx % 8)
              f.write((0).to_bytes(pad, "big"))
              idx += pad

